import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import EstimationSession, Participant


class SessionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time session updates"""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')

        # Broadcast to all clients in the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'session_update',
                'message': data
            }
        )

    async def session_update(self, event):
        """Handle session update messages"""
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))
