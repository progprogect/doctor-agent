# Application Load Balancer (optional - disabled by default for MVP)
resource "aws_lb" "main" {
  count              = var.enable_alb ? 1 : 0
  name               = "doctor-agent-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = merge(
    local.common_tags,
    {
      Name = "doctor-agent-alb"
    }
  )
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  count       = var.enable_alb ? 1 : 0
  name        = "doctor-agent-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "doctor-agent-alb-sg"
    }
  )
}

# Security Group rule: Allow ALB to access ECS service
resource "aws_security_group_rule" "alb_to_ecs" {
  count                    = var.enable_alb ? 1 : 0
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb[0].id
  security_group_id        = aws_security_group.ecs_service.id
  description              = "Allow ALB to access ECS service"
}

# Target Group for backend
resource "aws_lb_target_group" "backend" {
  count       = var.enable_alb ? 1 : 0
  name        = "doctor-agent-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  # Enable stickiness for WebSocket connections
  stickiness {
    enabled         = true
    type            = "lb_cookie"
    cookie_duration = 86400
  }

  deregistration_delay = 30

  tags = local.common_tags
}

# Target Group for Frontend
resource "aws_lb_target_group" "frontend" {
  count       = var.enable_alb ? 1 : 0
  name        = "doctor-agent-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = local.common_tags
}

# Security Group rule: Allow ALB to access Frontend
resource "aws_security_group_rule" "alb_to_frontend" {
  count                    = var.enable_alb ? 1 : 0
  type                     = "ingress"
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb[0].id
  security_group_id        = aws_security_group.ecs_service.id
  description              = "Allow ALB to access Frontend"
}

# HTTP Listener - Default action forwards to frontend
resource "aws_lb_listener" "frontend" {
  count             = var.enable_alb ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend[0].arn
  }
}

# HTTP Listener Rule - API routes go to backend
resource "aws_lb_listener_rule" "backend_api" {
  count        = var.enable_alb ? 1 : 0
  listener_arn = aws_lb_listener.frontend[0].arn
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

# HTTP Listener Rule - WebSocket routes go to backend
resource "aws_lb_listener_rule" "backend_websocket" {
  count        = var.enable_alb ? 1 : 0
  listener_arn = aws_lb_listener.frontend[0].arn
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

