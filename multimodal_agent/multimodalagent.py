from dotenv import load_dotenv
from multimodal_agent.usch_prompts import SYSTEM_PROMPT, EINFUEHRUNG
from livekit import agents
from livekit import rtc, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, get_job_context, RunContext
from livekit.plugins import openai
import logging
import openpyxl # Import the library
from pathlib import Path # To handle file paths

load_dotenv()

logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)

# Define the Excel file path
EXCEL_FILE_PATH = Path(__file__).parent / "collected_emails.xlsx"

def store_email_to_excel(email: str):
    """Appends a new email address to the Excel file."""
    try:
        # Load workbook or create if it doesn't exist
        if EXCEL_FILE_PATH.exists():
            workbook = openpyxl.load_workbook(EXCEL_FILE_PATH)
            sheet = workbook.active
        else:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.append(["Email Address"]) # Add header row

        # Append the new email
        sheet.append([email])

        # Save the workbook
        workbook.save(EXCEL_FILE_PATH)
        logger.info(f"Successfully stored email: {email} in {EXCEL_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to store email {email} in Excel: {e}")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def on_enter(self) -> None:
        # Use the EINFUEHRUNG from prompts as the initial instruction
        await self.session.generate_reply(instructions=EINFUEHRUNG)

    @function_tool(
        description="Call this function ONLY AFTER you have successfully obtained and confirmed the user's email address. Provide the confirmed email address.", # Updated description
    )
    async def end_call(self, email: str) -> None: # Added email parameter
        """Function to end the call after obtaining the email."""
        logger.info(f"Attempting to store email: {email}")
        store_email_to_excel(email) # Store the email

        # Generate final goodbye message
        await self.session.generate_reply(
            instructions="Verabschiede dich jetzt freundlich vom Benutzer und beende das Gespräch.",
        )
        # Consider adding a short delay before hanging up if needed
        # await asyncio.sleep(2)
        await self.hangup() # Hang up the call

    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""
        logger.info("Hanging up the call...")
        try:
            job_ctx = get_job_context()
            await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")

    @function_tool
    async def detected_answering_machine(self, ctx: RunContext):
        """"Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting."""
        logger.info("Detected voicemail")
        await self.hangup()

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="shimmer"),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(),
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))