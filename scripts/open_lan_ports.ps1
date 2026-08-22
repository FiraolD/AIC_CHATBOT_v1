# Adds inbound firewall rules for the Awash AI chatbot servers (one-shot, admin)
New-NetFirewallRule -DisplayName 'Awash AI Backend (TCP 8000)' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
New-NetFirewallRule -DisplayName 'Awash AI Frontend (TCP 3020)' -Direction Inbound -Protocol TCP -LocalPort 3020 -Action Allow -Profile Any
