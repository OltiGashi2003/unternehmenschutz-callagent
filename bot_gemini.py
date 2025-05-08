from livekit.plugins import google
from dotenv import load_dotenv
from gemini_prompts import SYSTEM_PROMPT, EINFUEHRUNG
from livekit import agents
from livekit import rtc, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, get_job_context, RunContext
from livekit.plugins import openai
import logging
import openpyxl # Import the library
from pathlib import Path # To handle file paths

load_dotenv()
logger = logging.getLogger("voicebot")
logger.setLevel(logging.INFO)

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
            sheet.append(["Email Address"])  # Add header row
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
    
    @function_tool()
    async def on_enter(self) -> None:
        """
        This method ensures the bot starts the conversation with the EINFUEHRUNG prompt
        """
        logger.info("on_enter method called. Bot is starting the conversation.")
        await self.session.generate_reply(instructions=EINFUEHRUNG)
        
    @function_tool()
    async def collect_email(self, email: str) -> None:
        """
        Collects the user's email address and stores it, called after confirming with the user.
        """
        # Store the email directly
        logger.info(f"Storing email: {email}")
        store_email_to_excel(email)
        
    @function_tool()
    async def ask_questions(self) -> None:
        """
        Wird aufgerufen, um den Nutzer zu fragen, ob noch weitere Fragen bestehen, nachdem er die E-Mail-Adresse gezeigt hat, und verarbeitet die Antwort entsprechend.
        """
        logger.info(f"Asking the user if they have any questions")
        # Generate a reply to ask if the user has further questions
        await self.session.generate_reply(
            instructions="Haben Sie noch weitere Fragen, die ich beantworten kann?"
        )
    async def hangup(self) -> None:
        logger.info("Hanging up the call...")
        try:
            job_ctx = get_job_context()
            await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            
    @function_tool()
    async def end_call(self, ctx: RunContext):
        """
        Wird aufgerufen, wenn der Kunde sich verabschiedet hat, indem er "Auf Wiedersehen", "Tschüss", "Ciao" oder ähnliche Abschiedsfloskeln sagt. 
        Diese Funktion wird verwendet, um den Anruf zu beenden, nachdem der Kunde sich verabschiedet hat.
        Wird aufgerufen wenn der Kunde die Anrufe beenden will.
        Wird aufgerufen wenn der Kunde kein Interesse hat. 
        """

        logger.info("ending the call for {self.participant.identity}")
        await self.hangup()
        
    @function_tool
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail."""
        logger.info("Detected voicemail")
        await self.hangup()
        
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Aoede",  # Ensure this voice supports German
            temperature=0.8,
            instructions=SYSTEM_PROMPT,
            language="de-DE",
            # modalities=["Text", "Audio"],
    ))

    await session.start(
        room = ctx.room,
        agent=Assistant(),
    )
    
    await session.generate_reply(instructions=EINFUEHRUNG)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))