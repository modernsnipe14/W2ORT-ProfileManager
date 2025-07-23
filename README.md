# W2ORT-ProfileManager
Custom Profiles for Discord - Specific to HAM Radio


Installation Guide:
1. Create a discord bot application
2. In the Developer Portal, go to OAuth2 → URL Generator.
      Under Scopes, check:
       - bot
       - applications.commands

      Under Bot Permissions, check:
       - Send Messages
       - Embed Links
       - Read Message History
       - Slash Comamnds

      Copy the generated URL, open it in a browser, and invite the bot to your server.

3. pipx install -U discord.py

4. Create Script and modify script to include your bot token

5. 	cd /home/name
	source botenv/bin/activate
	python bot.py
	
6. /home/name/botenv/bin/python

7. sudo nano /etc/systemd/system/profilebot.service

paste the following:

[Unit]
Description=Discord Profile Bot
After=network.target

[Service]
Type=simple
User=astrousr
WorkingDirectory=/home/astrousr
ExecStart=/home/astrousr/botenv/bin/python /home/astrousr/bot.py
Restart=always

[Install]
WantedBy=multi-user.target

8. 	sudo systemctl daemon-reload
	sudo systemctl enable profilebot.service
	sudo systemctl start profilebot.service

9. Use commands:

/profile_edit (Username)
/profile_view (Username)
/profile_addfield (Field Name)
/profile_removefield (Field Name)
