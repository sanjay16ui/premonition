output "vpc_id" { value = aws_vpc.main.id }
output "eks_cluster_name" { value = aws_eks_cluster.main.name }
output "rds_endpoint" { value = aws_db_instance.main.endpoint }
output "s3_bucket_name" { value = aws_s3_bucket.data.id }
output "secrets_arn" { value = aws_secretsmanager_secret.db_credentials.arn }
output "cloudfront_domain" { value = try(aws_cloudfront_distribution.cdn[0].domain_name, null) }
output "waf_arn" { value = try(aws_wafv2_web_acl.main[0].arn, null) }
