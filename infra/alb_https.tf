# HTTPS Listener for ALB (required for Instagram webhook)
# Note: Instagram requires HTTPS for webhook verification

# HTTPS Listener for ALB (required for Instagram webhook)
# Note: Instagram requires HTTPS for webhook verification
# 
# Certificate ARN: arn:aws:acm:me-central-1:760221990195:certificate/fb01239b-42b6-43b0-8325-855d6a9d0247
# This certificate was imported manually via AWS CLI (self-signed certificate)
# For production, use a proper domain-based certificate from ACM or Let's Encrypt

# HTTPS Listener - Default action forwards to frontend
# Using imported self-signed certificate ARN
resource "aws_lb_listener" "frontend_https" {
  count             = var.enable_alb ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  # Using imported certificate ARN (created manually via AWS CLI)
  certificate_arn   = "arn:aws:acm:me-central-1:760221990195:certificate/fb01239b-42b6-43b0-8325-855d6a9d0247"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend[0].arn
  }
}

# HTTPS Listener Rule - API routes go to backend
resource "aws_lb_listener_rule" "backend_api_https" {
  count        = var.enable_alb ? 1 : 0
  listener_arn = aws_lb_listener.frontend_https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend[0].arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health", "/docs", "/openapi.json"]
    }
  }
}

# HTTPS Listener Rule - WebSocket routes go to backend
resource "aws_lb_listener_rule" "backend_websocket_https" {
  count        = var.enable_alb ? 1 : 0
  listener_arn = aws_lb_listener.frontend_https[0].arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend[0].arn
  }

  condition {
    path_pattern {
      values = ["/ws/*"]
    }
  }
}

# HTTP to HTTPS redirect is now handled in alb.tf
# This file only contains HTTPS listener configuration

