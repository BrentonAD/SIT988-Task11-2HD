from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    ConversationState,
    UserState
)
from botbuilder.schema import (
    ChannelAccount
)

from data_models import ConversationData, UserProfile
from api.request_handler import get_user, get_user_allergies
from dialogs import WelcomeNewUserDialog, ProvideIngredientsDialog
from helpers import DialogHelper

from typing import List

class RecipeBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[RecipeBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[RecipeBot]: Missing parameter. user_state is required but None was given"
            )

        self._conversation_state = conversation_state
        self._user_state = user_state

        self.conversation_data_accessor = self._conversation_state.create_property(
            "ConversationData"
        )        
        self.user_profile_accessor = self._user_state.create_property("UserProfile")

        self.WELCOME_MESSAGE = """Welcome to RecipeBot, where you can provide your ingredients
                        and receive a tailored recipe.
                        Let's help reduce food waste together!"""

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        # save changes to WelcomeUserState after each turn
        await self._conversation_state.save_changes(turn_context)
        await self._user_state.save_changes(turn_context)

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """
        Greet when users are added to the conversation.
        Note that all channels do not send the conversation update activity.
        If you find that this bot works in the emulator, but does not in
        another channel the reason is most likely that the channel does not
        send this activity.
        """
        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )

        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Hi there { member.name }. " + self.WELCOME_MESSAGE
                )
                
                # Get user from database
                user = get_user(member.id)
                if not user:
                    user_profile.id = member.id
                    user_profile.name = member.name
                    await DialogHelper.run_dialog(
                        WelcomeNewUserDialog(self._user_state, self._conversation_state),
                        turn_context,
                        self._conversation_state.create_property("WelcomeNewUserDialogState")
                    )
                else:
                    allergies = get_user_allergies(user.get("id"))
                    user_profile.id = user.get("id")
                    user_profile.name = user.get("name")
                    user_profile.allergies = allergies
                    user_profile.allow_tracking = True
                    conversation_data.did_welcome=True

                    await turn_context.send_activity(f"Welcome back {user_profile.name}!")
                    if allergies:
                        if len(allergies)>1:
                            allergies_msg = ", ".join(allergies[:-1]) + ", and " + allergies[-1]
                        else:
                            allergies_msg = allergies[0]
                        await turn_context.send_activity(f"You previously said you were allergic to: {allergies_msg}")
                    await DialogHelper.run_dialog(
                        ProvideIngredientsDialog(self._user_state, self._conversation_state),
                        turn_context,
                        self._conversation_state.create_property("ProvideIngredientsDialog")
                    )
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Respond to messages sent from the user.
        """
        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )
        if conversation_data.did_welcome:
            await DialogHelper.run_dialog(
                ProvideIngredientsDialog(self._user_state, self._conversation_state),
                    turn_context,
                    self._conversation_state.create_property("ProvideIngredientsDialog")
                )
        else:
            await DialogHelper.run_dialog(
                WelcomeNewUserDialog(self._user_state, self._conversation_state),
                    turn_context,
                    self._conversation_state.create_property("WelcomeNewUserDialogState")
                )
