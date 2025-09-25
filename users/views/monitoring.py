"""
Security monitoring dashboard views for administrators.
"""
import logging
from datetime import timedelta
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from users.models import SecurityLog, User
from users.services.security import SecurityService

logger = logging.getLogger(__name__)


@staff_member_required
def security_dashboard(request):
    """
    Security monitoring dashboard for administrators.
    """
    try:
        # Get time ranges
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Get security statistics
        stats = {
            'total_events_24h': SecurityLog.objects.filter(created_at__gte=last_24h).count(),
            'total_events_7d': SecurityLog.objects.filter(created_at__gte=last_7d).count(),
            'total_events_30d': SecurityLog.objects.filter(created_at__gte=last_30d).count(),
            
            'failed_logins_24h': SecurityLog.objects.filter(
                event_type='login_failed',
                created_at__gte=last_24h
            ).count(),
            
            'suspicious_activities_24h': SecurityLog.objects.filter(
                event_type='suspicious_activity',
                created_at__gte=last_24h
            ).count(),
            
            'rate_limit_violations_24h': SecurityLog.objects.filter(
                event_type='rate_limit_exceeded',
                created_at__gte=last_24h
            ).count(),
            
            'account_locks_24h': SecurityLog.objects.filter(
                event_type='login_locked',
                created_at__gte=last_24h
            ).count(),
            
            'high_severity_events_24h': SecurityLog.objects.filter(
                severity__in=['high', 'critical'],
                created_at__gte=last_24h
            ).count(),
        }
        
        # Get top IPs with most events
        top_ips = SecurityLog.objects.filter(
            created_at__gte=last_24h
        ).values('ip_address').annotate(
            event_count=Count('id')
        ).order_by('-event_count')[:10]
        
        # Get recent high-severity events
        recent_high_severity = SecurityLog.objects.filter(
            severity__in=['high', 'critical'],
            created_at__gte=last_7d
        ).select_related('user').order_by('-created_at')[:20]
        
        # Get event type distribution
        event_distribution = SecurityLog.objects.filter(
            created_at__gte=last_24h
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Get locked users
        locked_users = User.objects.filter(
            locked_until__gt=now
        ).order_by('-locked_until')[:10]
        
        context = {
            'stats': stats,
            'top_ips': top_ips,
            'recent_high_severity': recent_high_severity,
            'event_distribution': event_distribution,
            'locked_users': locked_users,
            'page_title': 'Security Monitoring Dashboard'
        }
        
        return render(request, 'admin/security_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in security dashboard: {str(e)}")
        return render(request, 'admin/security_dashboard.html', {
            'error': 'Unable to load security dashboard data.',
            'page_title': 'Security Monitoring Dashboard'
        })


@staff_member_required
def security_logs_api(request):
    """
    API endpoint for security logs data (for AJAX requests).
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))
        event_type = request.GET.get('event_type', '')
        severity = request.GET.get('severity', '')
        ip_address = request.GET.get('ip_address', '')
        user_id = request.GET.get('user_id', '')
        days = int(request.GET.get('days', 7))
        
        # Build query
        since_date = timezone.now() - timedelta(days=days)
        queryset = SecurityLog.objects.filter(created_at__gte=since_date)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Order by created_at descending
        queryset = queryset.select_related('user').order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        logs_data = []
        for log in page_obj:
            logs_data.append({
                'id': log.id,
                'event_type': log.event_type,
                'event_type_display': log.get_event_type_display(),
                'severity': log.severity,
                'severity_display': log.get_severity_display(),
                'user': {
                    'id': str(log.user.id) if log.user else None,
                    'username': log.user.username if log.user else 'Anonymous',
                    'email': log.user.email if log.user else None,
                } if log.user else None,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'details': log.details,
                'created_at': log.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        logger.error(f"Error in security logs API: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to fetch security logs data.'
        }, status=500)


@staff_member_required
def security_stats_api(request):
    """
    API endpoint for security statistics (for dashboard charts).
    """
    try:
        days = int(request.GET.get('days', 7))
        since_date = timezone.now() - timedelta(days=days)
        
        # Get hourly event counts for the chart
        hourly_stats = []
        for i in range(24):
            hour_start = timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            count = SecurityLog.objects.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).count()
            
            hourly_stats.append({
                'hour': hour_start.strftime('%H:00'),
                'count': count
            })
        
        # Reverse to show oldest to newest
        hourly_stats.reverse()
        
        # Get severity distribution
        severity_stats = SecurityLog.objects.filter(
            created_at__gte=since_date
        ).values('severity').annotate(
            count=Count('id')
        ).order_by('severity')
        
        # Get event type distribution
        event_type_stats = SecurityLog.objects.filter(
            created_at__gte=since_date
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'success': True,
            'hourly_stats': hourly_stats,
            'severity_stats': list(severity_stats),
            'event_type_stats': list(event_type_stats),
        })
        
    except Exception as e:
        logger.error(f"Error in security stats API: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to fetch security statistics.'
        }, status=500)


@staff_member_required
def unlock_user_account(request):
    """
    API endpoint to unlock a user account.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        user_id = request.POST.get('user_id')
        reason = request.POST.get('reason', 'Manual unlock by admin')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User ID is required'})
        
        user = User.objects.get(id=user_id)
        ip_address = SecurityService.get_client_ip(request)
        
        # Unlock the account
        success = SecurityService.unlock_user_account(
            user=user,
            ip_address=ip_address,
            reason=f"{reason} (by {request.user.username})"
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'User {user.username} has been unlocked successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to unlock user account.'
            })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        logger.error(f"Error unlocking user account: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})


@staff_member_required
def block_ip_address(request):
    """
    API endpoint to block an IP address.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        ip_address = request.POST.get('ip_address')
        duration_minutes = int(request.POST.get('duration_minutes', 60))
        reason = request.POST.get('reason', 'Manual block by admin')
        
        if not ip_address:
            return JsonResponse({'success': False, 'error': 'IP address is required'})
        
        # Block the IP
        success = SecurityService.block_ip(
            ip_address=ip_address,
            duration_minutes=duration_minutes,
            reason=f"{reason} (by {request.user.username})"
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'IP {ip_address} has been blocked for {duration_minutes} minutes.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to block IP address.'
            })
        
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid duration value'})
    except Exception as e:
        logger.error(f"Error blocking IP address: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})