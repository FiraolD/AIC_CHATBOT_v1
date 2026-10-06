# Adds inbound firewall rules for the smart AI chatbot servers (one-shot, admin)
New-NetFirewallRule -DisplayName 'smart AI Backend (TCP 8000)' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
New-NetFirewallRule -DisplayName 'smart AI Frontend (TCP 3020)' -Direction Inbound -Protocol TCP -LocalPort 3020 -Action Allow -Profile Any
