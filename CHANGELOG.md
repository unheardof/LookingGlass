# 6-12-2023

Migrated the data_value column in the additional_node_data table from a varchar column to a text column using the following steps:

1. Connect to MySQL using the password which was set when the cluster was initialized: `./scripts/mysql_shell.sh`
1. Switch to the looking_glass database: `USE looking_glass;`
1. View the current table schema: `DESCRIBE additional_node_data;`
1. Update the table schema: `ALTER TABLE additional_node_data MODIFY data_value TEXT NULL DEFAULT NULL;`
1. Confirm change succeeded: `DESCRIBE additional_node_data;`
