from fake_useragent import UserAgent

# Initialize UserAgent
ua = UserAgent()

# Attempt to update the data to get the latest user agents
try:
    ua.update()
except Exception as e:
    print(f"Note: Failed to update user agents data. Using cached version. Error: {e}")

# Use a set to avoid duplicates
all_user_agents = set()

# Extract user agents from each browser category
for browser in ua.data:
    for entry in ua.data[browser]:
        user_agent = entry.get('useragent')
        if user_agent:
            all_user_agents.add(user_agent)

# Write to a text file
with open('user_agents.txt', 'w') as f:
    for user_agent in sorted(all_user_agents):
        f.write(f"{user_agent}\n")

print(f"Successfully saved {len(all_user_agents)} unique user agents to 'user_agents.txt'.")