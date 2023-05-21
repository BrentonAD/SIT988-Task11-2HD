from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    MessageFactory,
    ConversationState,
    UserState
)
from botbuilder.schema import (
    ChannelAccount,
    CardAction,
    ActionTypes,
    SuggestedActions
)

from data_models import ConversationData, UserProfile
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

    async def _send_tracking_permission_card(self, turn_context: TurnContext):

        reply = MessageFactory.text(
            "Do you consent to your name, allergies, and recipe preferences being tracked?"
            "This will help tailor your experiences in the future."
            )
        reply.suggested_actions = SuggestedActions(
            actions=[
                CardAction(
                    title="Yes",
                    type=ActionTypes.im_back,
                    value="Yes"
                ),
                CardAction(
                    title="No",
                    type=ActionTypes.im_back,
                    value="No"
                )
            ]
        )

        return await turn_context.send_activity(reply)

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

        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Hi there { member.name }. " + self.WELCOME_MESSAGE
                )
                
                user_profile.id = member.id
                user_profile.name = member.name

                await turn_context.send_activity("Before we get started, please answer the following question...")

                await self._send_tracking_permission_card(turn_context)
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Respond to messages sent from the user.
        """
        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )

        if not conversation_data.did_prompt_for_tracking:
            conversation_data.did_prompt_for_tracking = True
            response = turn_context.activity.text
            if response == "Yes":
                user_profile.allow_tracking = True
                await turn_context.send_activity(
                    f"Okay {user_profile.name}, your preferences will be tracked for future use!"
                )
            elif response == "No":
                await turn_context.send_activity(
                    f"Okay {user_profile.name}, your preferences will not be tracked beyond this conversation."
                )
            else:
                conversation_data.did_prompt_for_tracking = False
                await turn_context.send_activity("Please select from the given options.")
                await self._send_tracking_permission_card(turn_context)
            
        else:
            await turn_context.send_activity("That is the end of this flow")
