# ===========================================
# Monitoring Module - Logging & Monitoring
# ===========================================

variable "project_id" {
  type = string
}

variable "backend_service_name" {
  type = string
}

variable "frontend_service_name" {
  type = string
}

variable "celery_service_name" {
  type = string
}

variable "notification_email" {
  type = string
}

# ===========================================
# Notification Channel
# ===========================================
resource "google_monitoring_notification_channel" "email" {
  display_name = "Call Quality Dashboard Alerts"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.notification_email
  }
}

# ===========================================
# Log-based Metrics
# ===========================================

# Error rate metric
resource "google_logging_metric" "error_count" {
  name    = "call-quality/error-count"
  project = var.project_id
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name=~"call-quality-.*"
    severity>=ERROR
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "service_name"
      value_type  = "STRING"
      description = "Cloud Run service name"
    }
  }

  label_extractors = {
    "service_name" = "EXTRACT(resource.labels.service_name)"
  }
}

# Batch job failure metric
resource "google_logging_metric" "batch_failure" {
  name    = "call-quality/batch-failure"
  project = var.project_id
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="call-quality-backend"
    jsonPayload.event="batch_failed"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# ===========================================
# Alert Policies
# ===========================================

# High error rate alert
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Call Quality - High Error Rate"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 10 per minute"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.labels.service_name"]
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "High error rate detected in Call Quality Dashboard services. Please check Cloud Run logs for details."
    mime_type = "text/markdown"
  }
}

# Service down alert
resource "google_monitoring_alert_policy" "service_down" {
  display_name = "Call Quality - Service Down"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Backend service not responding"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"call-quality-backend\" AND metric.type = \"run.googleapis.com/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_COUNT"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "Backend service appears to be down. No requests received in the last 5 minutes."
    mime_type = "text/markdown"
  }
}

# Batch job failure alert
resource "google_monitoring_alert_policy" "batch_failure" {
  display_name = "Call Quality - Batch Job Failed"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Batch job failed"

    condition_threshold {
      filter          = "metric.type = \"logging.googleapis.com/user/call-quality/batch-failure\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "86400s"  # 24 hours
  }

  documentation {
    content   = <<-EOT
      # Batch Job Failed

      The daily batch job to fetch call data from Biztel has failed.

      ## Action Required
      1. Check Cloud Run logs for error details
      2. Verify Biztel API credentials are valid
      3. Note: Biztel recordings are only retained for 7 days
      4. Manual recovery may be required: POST /api/batch/recovery
    EOT
    mime_type = "text/markdown"
  }
}

# High latency alert
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Call Quality - High Latency"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "P99 latency > 5 seconds"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"call-quality-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000  # 5 seconds in milliseconds

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "High latency detected in backend service. P99 latency exceeds 5 seconds."
    mime_type = "text/markdown"
  }
}

# ===========================================
# Dashboard
# ===========================================
resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "Call Quality Dashboard"
    gridLayout = {
      columns = 2
      widgets = [
        {
          title = "Request Count by Service"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name =~ \"call-quality-.*\" AND metric.type = \"run.googleapis.com/request_count\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_SUM"
                    groupByFields      = ["resource.labels.service_name"]
                  }
                }
              }
            }]
          }
        },
        {
          title = "Error Rate"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name =~ \"call-quality-.*\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_SUM"
                    groupByFields      = ["resource.labels.service_name"]
                  }
                }
              }
            }]
          }
        },
        {
          title = "Request Latency (P50/P95/P99)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"call-quality-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_PERCENTILE_50"
                    }
                  }
                }
                legendTemplate = "P50"
              },
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"call-quality-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_PERCENTILE_95"
                    }
                  }
                }
                legendTemplate = "P95"
              },
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"call-quality-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_PERCENTILE_99"
                    }
                  }
                }
                legendTemplate = "P99"
              }
            ]
          }
        },
        {
          title = "Container Instance Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name =~ \"call-quality-.*\" AND metric.type = \"run.googleapis.com/container/instance_count\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_MEAN"
                    crossSeriesReducer = "REDUCE_SUM"
                    groupByFields      = ["resource.labels.service_name"]
                  }
                }
              }
            }]
          }
        },
        {
          title = "Memory Utilization"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name =~ \"call-quality-.*\" AND metric.type = \"run.googleapis.com/container/memory/utilizations\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_MEAN"
                    crossSeriesReducer = "REDUCE_MEAN"
                    groupByFields      = ["resource.labels.service_name"]
                  }
                }
              }
            }]
          }
        },
        {
          title = "CPU Utilization"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name =~ \"call-quality-.*\" AND metric.type = \"run.googleapis.com/container/cpu/utilizations\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_MEAN"
                    crossSeriesReducer = "REDUCE_MEAN"
                    groupByFields      = ["resource.labels.service_name"]
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
  project = var.project_id
}

# ===========================================
# Outputs
# ===========================================
output "notification_channel_id" {
  value = google_monitoring_notification_channel.email.name
}

output "dashboard_id" {
  value = google_monitoring_dashboard.main.id
}
