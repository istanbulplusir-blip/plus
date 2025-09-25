/**
 * CSS Performance Monitoring
 * Tracks CSS loading performance and reports metrics
 */

(function() {
    'use strict';
    
    // Performance monitoring configuration
    const config = {
        enabled: true,
        reportEndpoint: '/api/performance/css/',
        sampleRate: 0.1, // Report 10% of page loads
        maxReportSize: 1000 // Maximum number of entries to report
    };
    
    // Check if performance monitoring is supported
    if (!window.performance || !window.performance.getEntriesByType) {
        return;
    }
    
    // CSS Performance Monitor
    class CSSPerformanceMonitor {
        constructor() {
            this.metrics = {};
            this.startTime = performance.now();
            this.init();
        }
        
        init() {
            // Mark CSS loading start
            if (performance.mark) {
                performance.mark('css-loading-start');
            }
            
            // Monitor when CSS files finish loading
            this.monitorCSSLoading();
            
            // Monitor critical CSS rendering
            this.monitorCriticalCSS();
            
            // Report metrics when page is fully loaded
            window.addEventListener('load', () => {
                setTimeout(() => this.collectAndReport(), 100);
            });
        }
        
        monitorCSSLoading() {
            // Monitor external CSS files
            const cssLinks = document.querySelectorAll('link[rel="stylesheet"], link[rel="preload"][as="style"]');
            let loadedCount = 0;
            const totalCount = cssLinks.length;
            
            cssLinks.forEach((link, index) => {
                const startTime = performance.now();
                
                const onLoad = () => {
                    const loadTime = performance.now() - startTime;
                    this.recordMetric(`css_file_${index}`, {
                        url: link.href,
                        loadTime: loadTime,
                        size: this.estimateFileSize(link),
                        critical: link.hasAttribute('data-critical') || link.rel === 'preload'
                    });
                    
                    loadedCount++;
                    if (loadedCount === totalCount) {
                        this.recordMetric('all_css_loaded', {
                            totalFiles: totalCount,
                            totalTime: performance.now() - this.startTime
                        });
                    }
                };
                
                const onError = () => {
                    this.recordMetric(`css_error_${index}`, {
                        url: link.href,
                        error: 'Failed to load'
                    });
                };
                
                if (link.sheet) {
                    // Already loaded
                    onLoad();
                } else {
                    link.addEventListener('load', onLoad);
                    link.addEventListener('error', onError);
                }
            });
        }
        
        monitorCriticalCSS() {
            // Monitor First Contentful Paint (FCP)
            if (window.PerformanceObserver) {
                try {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        entries.forEach((entry) => {
                            if (entry.name === 'first-contentful-paint') {
                                this.recordMetric('first_contentful_paint', {
                                    time: entry.startTime,
                                    critical_css_impact: this.calculateCriticalCSSImpact(entry.startTime)
                                });
                            }
                        });
                    });
                    
                    observer.observe({ entryTypes: ['paint'] });
                } catch (e) {
                    // PerformanceObserver not supported
                }
            }
        }
        
        calculateCriticalCSSImpact(fcpTime) {
            // Estimate impact of critical CSS on FCP
            const criticalCSSSize = this.estimateCriticalCSSSize();
            const estimatedImpact = criticalCSSSize > 0 ? Math.max(0, 200 - (criticalCSSSize / 100)) : 0;
            
            return {
                estimated_improvement_ms: estimatedImpact,
                critical_css_size: criticalCSSSize,
                fcp_time: fcpTime
            };
        }
        
        estimateCriticalCSSSize() {
            // Estimate critical CSS size from inline styles
            const inlineStyles = document.querySelectorAll('style');
            let totalSize = 0;
            
            inlineStyles.forEach((style) => {
                if (style.textContent) {
                    totalSize += style.textContent.length;
                }
            });
            
            return totalSize;
        }
        
        estimateFileSize(link) {
            // Try to get file size from resource timing
            const resourceEntries = performance.getEntriesByName(link.href);
            if (resourceEntries.length > 0) {
                const entry = resourceEntries[0];
                return entry.transferSize || entry.encodedBodySize || 0;
            }
            return 0;
        }
        
        recordMetric(name, data) {
            this.metrics[name] = {
                ...data,
                timestamp: performance.now(),
                url: window.location.href
            };
        }
        
        collectAndReport() {
            // Collect additional performance metrics
            this.collectResourceTimingMetrics();
            this.collectNavigationMetrics();
            
            // Add summary metrics
            this.metrics.summary = this.calculateSummaryMetrics();
            
            // Report metrics (with sampling)
            if (Math.random() < config.sampleRate && config.enabled) {
                this.reportMetrics();
            }
            
            // Log metrics to console in development
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.group('🎨 CSS Performance Metrics');
                console.table(this.metrics.summary);
                console.log('Full metrics:', this.metrics);
                console.groupEnd();
            }
        }
        
        collectResourceTimingMetrics() {
            const resourceEntries = performance.getEntriesByType('resource');
            const cssEntries = resourceEntries.filter(entry => 
                entry.name.includes('.css') || entry.initiatorType === 'css'
            );
            
            this.metrics.resource_timing = {
                total_css_files: cssEntries.length,
                total_css_size: cssEntries.reduce((sum, entry) => sum + (entry.transferSize || 0), 0),
                average_css_load_time: cssEntries.length > 0 
                    ? cssEntries.reduce((sum, entry) => sum + entry.duration, 0) / cssEntries.length 
                    : 0,
                css_files: cssEntries.map(entry => ({
                    name: entry.name,
                    size: entry.transferSize || entry.encodedBodySize || 0,
                    duration: entry.duration,
                    start_time: entry.startTime
                }))
            };
        }
        
        collectNavigationMetrics() {
            const navEntries = performance.getEntriesByType('navigation');
            if (navEntries.length > 0) {
                const nav = navEntries[0];
                this.metrics.navigation = {
                    dom_content_loaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
                    load_complete: nav.loadEventEnd - nav.loadEventStart,
                    total_page_load: nav.loadEventEnd - nav.navigationStart
                };
            }
        }
        
        calculateSummaryMetrics() {
            const resourceTiming = this.metrics.resource_timing || {};
            const navigation = this.metrics.navigation || {};
            
            return {
                'Total CSS Files': resourceTiming.total_css_files || 0,
                'Total CSS Size (KB)': Math.round((resourceTiming.total_css_size || 0) / 1024),
                'Average CSS Load Time (ms)': Math.round(resourceTiming.average_css_load_time || 0),
                'Critical CSS Size (KB)': Math.round(this.estimateCriticalCSSSize() / 1024),
                'First Contentful Paint (ms)': Math.round(this.metrics.first_contentful_paint?.time || 0),
                'DOM Content Loaded (ms)': Math.round(navigation.dom_content_loaded || 0),
                'Page Load Complete (ms)': Math.round(navigation.total_page_load || 0)
            };
        }
        
        reportMetrics() {
            // Send metrics to server (if endpoint is configured)
            if (!config.reportEndpoint) {
                return;
            }
            
            const payload = {
                metrics: this.metrics,
                user_agent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                connection: this.getConnectionInfo(),
                timestamp: new Date().toISOString()
            };
            
            // Use sendBeacon for reliable reporting
            if (navigator.sendBeacon) {
                navigator.sendBeacon(
                    config.reportEndpoint,
                    JSON.stringify(payload)
                );
            } else {
                // Fallback to fetch
                fetch(config.reportEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                    keepalive: true
                }).catch(() => {
                    // Ignore reporting errors
                });
            }
        }
        
        getConnectionInfo() {
            if (navigator.connection) {
                return {
                    effective_type: navigator.connection.effectiveType,
                    downlink: navigator.connection.downlink,
                    rtt: navigator.connection.rtt,
                    save_data: navigator.connection.saveData
                };
            }
            return null;
        }
    }
    
    // Initialize CSS performance monitoring
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new CSSPerformanceMonitor();
        });
    } else {
        new CSSPerformanceMonitor();
    }
    
    // Export for manual access
    window.CSSPerformanceMonitor = CSSPerformanceMonitor;
    
})();