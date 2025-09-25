"""
Management command to generate security reports.
"""
import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from users.models import SecurityLog, User
from users.services.security import SecurityService


class Command(BaseCommand):
    help = 'Generate security reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)'
        )
        
        parser.add_argument(
            '--severity',
            choices=['low', 'medium', 'high', 'critical'],
            help='Filter by severity level'
        )
        
        parser.add_argument(
            '--event-type',
            type=str,
            help='Filter by event type'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        output_format = options['format']
        output_file = options['output']
        severity_filter = options['severity']
        event_type_filter = options['event_type']
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        self.stdout.write(f'Generating security report for the last {days} days...')
        
        # Build queryset
        queryset = SecurityLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        
        if event_type_filter:
            queryset = queryset.filter(event_type=event_type_filter)
        
        # Generate report data
        report_data = self._generate_report_data(queryset, start_date, end_date)
        
        # Format and output report
        if output_format == 'json':
            report_content = self._format_json_report(report_data)
        else:
            report_content = self._format_text_report(report_data, days)
        
        # Output to file or stdout
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.stdout.write(
                self.style.SUCCESS(f'Security report saved to {output_file}')
            )
        else:
            self.stdout.write(report_content)
    
    def _generate_report_data(self, queryset, start_date, end_date):
        """Generate report data from queryset"""
        
        # Basic statistics
        total_events = queryset.count()
        
        # Events by severity
        severity_stats = queryset.values('severity').annotate(
            count=Count('id')
        ).order_by('severity')
        
        # Events by type
        event_type_stats = queryset.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Top IPs
        top_ips = queryset.values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Users with most events
        top_users = queryset.filter(
            user__isnull=False
        ).values(
            'user__username', 'user__email'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Daily breakdown
        daily_stats = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_start = timezone.make_aware(
                timezone.datetime.combine(current_date, timezone.datetime.min.time())
            )
            day_end = day_start + timedelta(days=1)
            
            day_count = queryset.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': day_count
            })
            
            current_date += timedelta(days=1)
        
        # Critical events
        critical_events = queryset.filter(
            severity__in=['high', 'critical']
        ).select_related('user').order_by('-created_at')[:20]
        
        # Failed login attempts
        failed_logins = queryset.filter(
            event_type='login_failed'
        ).count()
        
        # Suspicious activities
        suspicious_activities = queryset.filter(
            event_type='suspicious_activity'
        ).count()
        
        # Rate limit violations
        rate_limit_violations = queryset.filter(
            event_type='rate_limit_exceeded'
        ).count()
        
        # Account locks
        account_locks = queryset.filter(
            event_type='login_locked'
        ).count()
        
        # Currently locked users
        locked_users = User.objects.filter(
            locked_until__gt=timezone.now()
        ).count()
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date.date() - start_date.date()).days + 1
            },
            'summary': {
                'total_events': total_events,
                'failed_logins': failed_logins,
                'suspicious_activities': suspicious_activities,
                'rate_limit_violations': rate_limit_violations,
                'account_locks': account_locks,
                'currently_locked_users': locked_users
            },
            'severity_distribution': list(severity_stats),
            'event_type_distribution': list(event_type_stats),
            'top_ips': list(top_ips),
            'top_users': list(top_users),
            'daily_breakdown': daily_stats,
            'critical_events': [
                {
                    'id': event.id,
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'user': event.user.username if event.user else None,
                    'ip_address': event.ip_address,
                    'created_at': event.created_at.isoformat(),
                    'details': event.details
                }
                for event in critical_events
            ]
        }
    
    def _format_text_report(self, data, days):
        """Format report as text"""
        lines = []
        lines.append("=" * 60)
        lines.append("SECURITY REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Period
        lines.append(f"Report Period: {data['period']['start_date'][:10]} to {data['period']['end_date'][:10]} ({days} days)")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 20)
        summary = data['summary']
        lines.append(f"Total Events: {summary['total_events']}")
        lines.append(f"Failed Logins: {summary['failed_logins']}")
        lines.append(f"Suspicious Activities: {summary['suspicious_activities']}")
        lines.append(f"Rate Limit Violations: {summary['rate_limit_violations']}")
        lines.append(f"Account Locks: {summary['account_locks']}")
        lines.append(f"Currently Locked Users: {summary['currently_locked_users']}")
        lines.append("")
        
        # Severity Distribution
        lines.append("SEVERITY DISTRIBUTION")
        lines.append("-" * 25)
        for item in data['severity_distribution']:
            lines.append(f"{item['severity'].title()}: {item['count']}")
        lines.append("")
        
        # Top Event Types
        lines.append("TOP EVENT TYPES")
        lines.append("-" * 20)
        for item in data['event_type_distribution'][:10]:
            lines.append(f"{item['event_type']}: {item['count']}")
        lines.append("")
        
        # Top IPs
        lines.append("TOP IP ADDRESSES")
        lines.append("-" * 20)
        for item in data['top_ips']:
            lines.append(f"{item['ip_address']}: {item['count']} events")
        lines.append("")
        
        # Top Users
        if data['top_users']:
            lines.append("TOP USERS (by events)")
            lines.append("-" * 25)
            for item in data['top_users']:
                lines.append(f"{item['user__username']} ({item['user__email']}): {item['count']} events")
            lines.append("")
        
        # Daily Breakdown
        lines.append("DAILY BREAKDOWN")
        lines.append("-" * 18)
        for item in data['daily_breakdown']:
            lines.append(f"{item['date']}: {item['count']} events")
        lines.append("")
        
        # Critical Events
        if data['critical_events']:
            lines.append("RECENT CRITICAL EVENTS")
            lines.append("-" * 28)
            for event in data['critical_events'][:10]:
                user_info = f" ({event['user']})" if event['user'] else ""
                lines.append(f"{event['created_at'][:19]} - {event['event_type']} - {event['severity'].upper()}{user_info}")
                lines.append(f"  IP: {event['ip_address']}")
                if event['details']:
                    lines.append(f"  Details: {json.dumps(event['details'], ensure_ascii=False)}")
                lines.append("")
        
        lines.append("=" * 60)
        lines.append("End of Report")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _format_json_report(self, data):
        """Format report as JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)