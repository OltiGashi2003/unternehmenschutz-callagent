from livekit.agents import llm
import enum
from typing import Annotated
import logging
from db_driver import DatabaseDriver

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()

class ClientDetails(enum.Enum):
    Name = "name"
    Vorname = "vorname"
    Stadt = "stadt"
    Strasse = "strasse"
    Anzahl_paket = "anzahl_paket"
    Total = "total"
    

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        
        self._client_details = {
            ClientDetails.Name: "",
            ClientDetails.Vorname: "",
            ClientDetails.Stadt: "",
            ClientDetails.Strasse: "",
            ClientDetails.Anzahl_paket: "",
            ClientDetails.Total: ""
        }
    
    def get_client_str(self):
        client_str = ""
        for key, value in self._client_details.items():
            client_str += f"{key}: {value}\n"
            
        return client_str
    
    @llm.ai_callable(description="Suchen Sie einen Client anhand seines Namens")
    def lookup_client(self, name: Annotated[str, llm.TypeInfo(description="Der Name des zu suchenden Clients")]):
        logger.info("Kunden-Name nachschlagen: %s", name)
        
        result = DB.get_client_by_name(name)
        if result is None:
            return "Kunde nicht gefunden"
        
        self._client_details = {
            ClientDetails.Name: result.Name,
            ClientDetails.Vorname: result.Vorname,
            ClientDetails.Stadt: result.Stadt,
            ClientDetails.Strasse: result.Strasse,
            ClientDetails.Anzahl_paket: result.Anzahl_paket,
            ClientDetails.Total: result.Total
            
        }
        
        return f"Die Kundendaten sind: {self.get_client_str()}"
    
    @llm.ai_callable(description="Holen Sie sich die Details des aktuellen Kunden")
    def get_client_details(self):
        logger.info("Kundendetails abrufen")
        return f"Die Kundendaten sind: {self.get_client_str()}"
    
    @llm.ai_callable(description="Bestellung erstellen")
    def create_order(
        self, 
        name: Annotated[str, llm.TypeInfo(description="Der Name des Kunden")],
        vorname: Annotated[str, llm.TypeInfo(description="Der Vorname des Kunden")],
        stadt: Annotated[str, llm.TypeInfo(description="Die Stadt des Kunden")],
        strasse: Annotated[int, llm.TypeInfo(description="Der Straße des Kunden")],
        anzahl_paket: Annotated[str, llm.TypeInfo(description="Das Anzahlpaket des Kunde")],
        total: Annotated[int, llm.TypeInfo(description="Der Gesamtbetrag, den der Kunde zahlen muss")]
    ):
        logger.info("create order - name: %s, vorname: %s, stadt: %s, year: %s, anzahl_paket: %s, total: %s",  name, vorname, stadt, strasse, anzahl_paket, total)
        result = DB.create_order(name, vorname, stadt, strasse, anzahl_paket, total)
        if result is None:
            return "Die Bestellung konnte nicht erstellt werden"
        
        self._client_details = {
           ClientDetails.Name: result.Name,
            ClientDetails.Vorname: result.Vorname,
            ClientDetails.Stadt: result.Stadt,
            ClientDetails.Strasse: result.Strasse,
            ClientDetails.Anzahl_paket: result.Anzahl_paket,
            ClientDetails.Total: result.Total
        }
        
        return "bestellung erstellt!"
    
    def has_orderd(self):
        return self._client_details[ClientDetails.Name] != ""