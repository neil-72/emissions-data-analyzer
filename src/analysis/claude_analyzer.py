# Fixed from previous
response = self.client.messages.create(
    model="claude-3-sonnet-20240229",  # <-- Fixed model name
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    max_tokens=4096
)