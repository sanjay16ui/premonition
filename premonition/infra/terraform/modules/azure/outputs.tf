output "resource_group" { value = azurerm_resource_group.main.name }
output "aks_cluster_name" { value = azurerm_kubernetes_cluster.main.name }
output "postgres_fqdn" { value = azurerm_postgresql_flexible_server.main.fqdn }
output "storage_account" { value = azurerm_storage_account.main.name }
output "key_vault_uri" { value = azurerm_key_vault.main.vault_uri }
