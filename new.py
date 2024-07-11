class Customer:
    def __init__(self, firstname, lastname, phonenumber, email):
        self.firstname = firstname
        self.lastname = lastname
        self.phonenumber = phonenumber
        self.email = email
        # self.houses = {}  # Assuming this attribute exists to hold House objects

    # def add_house(self, house):
    #     self.houses.append(house)

    def to_dict(self):
        # Convert customer attributes to a dictionary
        # Convert each house object in self.houses to a dictionary as well
        return {
            'firstname': self.firstname,
            'lastname': self.lastname,
            'phonenumber': self.phonenumber,
            'email': self.email
            # 'houses': [house.to_dict() for house in self.houses]
        }
    def list_houses(self):
        return ', '.join(str(house) for house in self.houses) if self.houses else "No houses"

    def __str__(self):
        return (f"Customer: {self.firstname} {self.lastname}, "
                f"Phone: {self.phonenumber}, Email: {self.email}, "
        )
                # f"Houses: {self.list_houses()}")
    
# ----------------------------------------------------------------------------------------------------
    
class House:
    def __init__(self, address, city, state_code, zip_code):
        self.address = address
        self.city = city
        self.state_code = state_code
        self.zip_code = zip_code
        # Assume more attributes or methods as needed

    def to_dict(self):
        # Convert house attributes to a dictionary
        return {
            'address': self.address,
            'city': self.city,
            'state_code': self.state_code,
            'zip_code': self.zip_code
            # Include other attributes as needed
        }
    def add_chamber(self, chamber_number):
        new_chamber = Chamber(chamber_number)
        self.chambers.append(new_chamber)
        return new_chamber  # For further manipulation

    def list_chambers(self):
        return ', '.join(str(chamber) for chamber in self.chambers) if self.chambers else "No chambers"

    def __str__(self):
        return (f"{self.address}, {self.city}, {self.state_code} {self.zip_code}, "
                f"Chambers: {self.list_chambers()}")
    
# ----------------------------------------------------------------------------------------------------
    
class Chamber:
    def __init__(self, chamber_number):
        self.chamber_number = chamber_number

    def add_room(self, room_name):
        new_room = Room(room_name)
        self.rooms.append(new_room)
        return new_room  # For further manipulation

    def list_rooms(self):
        return ', '.join(str(room) for room in self.rooms) if self.rooms else "No rooms"

    def __str__(self):
        return f"Chamber {self.chamber_number} with rooms: {self.list_rooms()}"
    
# ----------------------------------------------------------------------------------------------------
    
class Material:
    def __init__(self, material_type, properties):
        self.material_type = material_type
        self.properties = properties if isinstance(properties, dict) else {}

    def __str__(self):
        return f"{self.material_type}: {self.properties}"

# ----------------------------------------------------------------------------------------------------

class Room:
    def __init__(self, room_name):
        self.room_name = room_name

    def add_material(self, material_type, properties):
        self.materials[material_type] = Material(material_type, properties)

    def list_materials(self):
        return ', '.join(str(material) for material in self.materials.values()) if self.materials else "No materials"

    def __str__(self):
        return f"Room: {self.room_name}, Materials: {self.list_materials()}"

# ----------------------------------------------------------------------------------------------------

class lookup:
    def Get_cx_info():
        # query for cx name, phone number, address 
        # and all other information to be displayed in the customer page
        pass