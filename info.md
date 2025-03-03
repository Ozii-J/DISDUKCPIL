To run the application and allow access from other devices, use the following command:
```bash
streamlit run MDN.py --server.address 0.0.0.0 --server.port 8501
```

1. Find your public IP address using a service like https://whatismyipaddress.com/
2. Configure port forwarding on your router to forward port 8501 to your machine's local IP address
   - Log in to your router's admin panel
   - Find the Port Forwarding section
   - Add a new rule for TCP/UDP port 8501 to your machine's local IP
3. Check your firewall settings:
   - Allow incoming connections on port 8501
   - Add an exception for Streamlit in your firewall
4. Test if the port is open using https://canyouseeme.org/
5. Access the application from any network using: http://36.73.212.232:8501


2. netstat -ano | findstr :8501

3. taskkill /PID 2708 /F
4. streamlit run MDN.py --server.address 0.0.0.0 --server.port 8501
5. ipconfig
6. http://192.168.1.33:8501

RUN .VENV ENVIRONMENT
.venv\Scripts\activate
