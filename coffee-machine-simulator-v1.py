import json
import os
import time

logo = r"""                                                                                         
 ,-----.        ,---. ,---.                  ,------.         ,--.,--.       ,--.       ,--.   
'  .--./ ,---. /  .-'/  .-' ,---.  ,---.     |  .-.  \  ,---. |  |`--' ,---. |  ,---. ,-'  '-. 
|  |    | .-. ||  `-,|  `-,| .-. :| .-. :    |  |  \  :| .-. :|  |,--.| .-. ||  .-.  |'-.  .-' 
'  '--'\' '-' '|  .-'|  .-'\   --.\   --.    |  '--'  /\   --.|  ||  |' '-' '|  | |  |  |  |   
 `-----' `---' `--'  `--'   `----' `----'    `-------'  `----'`--'`--'.`-  / `--' `--'  `--'   
                                                                      `---'                    
"""

RESOURCES = ['water', 'milk', 'coffee']

REFILL_HELP_MSG = '''You can refill:
"milk" or "m"
"water" or "w"
"coffee" or "c"

To go back to the main menu, type "x" or "back"
'''

ORDER_HELP_MSG = '''You can order:
"cappuccino" or "c"
"expresso" or "e"
"latte" or "l"

If you want to make a new custom drink,
  type "new" or "n"

If you want to make a custom drink you have made before, 
  type "custom" or "x"
'''

INTRO_HELP_MSG = '''order- to make an order
report - to view the resources in the coffee machine
refill - to refill some of the resources in the machine
collect - to collect earnings in the machine [OWNER ONLY]
off - to switch off the coffee machine
'''


def print_error(msg):
    print(f"\033[31m{msg}\033[0m", end="")


def get_data():
    with open("bin/data-v1.json", "r") as file1:
        data = json.load(file1)
    return data


def generate_report(data):
    print("-----REPORT-----")
    print("    Remaining Resources:")
    print(f"        Water  => {data['resources']['water']}/{data['max']['water']} ml")
    print(f"        Coffee => {data['resources']['coffee']}/{data['max']['coffee']} g")
    print(f"        Milk   => {data['resources']['milk']}/{data['max']['milk']}ml")
    print(f"    Accumulated Cash: ${data['resources']['money'] / 100 :.2f}")
    input(f"-----ENTER TO END OF REPORT-----")


def add_coffee(data):
    water = int_input("How much water(ml) does it have: ")
    coffee = int_input("How much coffee beans(g) does it have: ")
    milk = int_input("How much milk(ml) does it have: ")

    price = 0

    if water <= 200:
        price += 100
    elif water <= 250:
        price += 150
    else:
        price += ((water - 150) // 100) * 50

    price += (coffee // 50) * 50
    price += (milk // 50) * 50

    print(f"The price of this coffee is ${price / 100:.2f}")

    while True:
        coffee_name = input("Name the coffee: ").lower()
        if coffee_name != "" and coffee_name not in data["builtin-coffee"] and\
                coffee_name not in [custom["name"] for custom in data["custom-coffee"]]:
            break
        print_error("Invalid name\n")

    data["custom-coffee"].append({
        "name": coffee_name,
        "resources": {
            "water": water,
            "coffee": coffee,
            "milk": milk,
            "price": price
        }
    })

    input("---New coffee created. Enter to continue----")


def made_coffee(coffee, coffee_data, machine_resources):
    insufficient = []

    for i in RESOURCES:
        if coffee_data[i] > machine_resources[i]:
            insufficient.append(i)
    if len(insufficient) > 0:
        print_error(f"Insufficient amounts of \
{', '.join(insufficient[:-1])}{', and ' if len(insufficient) > 1 else ''}{insufficient[-1]}\
. Refill to make this coffee.\n")
        return

    print(f"Ok, this beverage would be ${coffee_data['price'] / 100 :.2f}")
    print("\nInsert coins:")
    pennies = int_input("Pennies: ")
    nickels = int_input("Nickels: ")
    dimes = int_input("Dimes: ")
    quarters = int_input("Quarters: ")

    cash_in_hand = pennies + (nickels * 5) + (dimes * 10) + (quarters * 25)
    if cash_in_hand == 0:
        print_error("No coins inserted. Order has been cancelled.\n")
        return

    if cash_in_hand < coffee_data["price"]:
        print_error(f"Insufficient funds. Refunding ${cash_in_hand / 100 :.2f}\n")
        return

    print("Coffee is served.", end="")
    if cash_in_hand > coffee_data["price"]:
        print(f"You have been refunded ${(cash_in_hand - coffee_data['price']) / 100 : .2f}", end="")
    print("\n")

    machine_resources["water"] -= coffee_data["water"]
    machine_resources["coffee"] -= coffee_data["coffee"]
    machine_resources["milk"] -= coffee_data["milk"]
    machine_resources["money"] += coffee_data["price"]


def input_from_choice(msg, choices, /, help_msg=None):
    choices = {str(choice): str(i) for i, x in choices.items() for choice in x}

    while True:
        ans = input(msg).lower().strip()
        if ans in choices or ans in choices.values():
            return choices[ans] if ans in choices else ans
        elif ans in ["help", "h"] and help_msg is not None:
            print("----HELP----")
            print(help_msg)
            input("---Enter to continue---")
            print()
        else:
            print_error(
                f"Invalid input. {'Type help to see all available commands.' if help_msg is not None else ''}\n")


def int_input(msg, positive=True):
    while True:
        ans = input(msg).strip()

        try:
            if ans == "": return 0
            ans = int(ans)

            if positive and ans < 0:
                print_error("Value must be positive\n")
            else:
                return ans
        except ValueError:
            print_error("Invalid input. Input must be an integer.\n")


def order_interface(data):
    coffee = input_from_choice("What would you like to order: ",
                               {"cappuccino": ["c"], "expresso": ["e"],
                                "latte": ["l"], 3: ["new", "n"], 4: ["custom", "x"]},
                               help_msg=ORDER_HELP_MSG
                               )

    match coffee:
        case x if x in data["builtin-coffee"]:
            coffee_specs = data["builtin-coffee"][x]
            made_coffee(coffee, coffee_specs, data["resources"])

        case '3':
            add_coffee(data)
            pass
        case '4':
            if not data["custom-coffee"]:
                print_error("No custom coffee recipe yet.")
            else:
                custom_coffee_choices, custom_coffee_menu = {}, []
                for i, coffee in enumerate(data["custom-coffee"]):
                    coffee_str = f"""\
{i + 1}. {coffee['name']} 
    [{coffee['resources']['water']}ml of water \
- {coffee['resources']['milk']}ml of milk \
- {coffee['resources']['coffee']}]"""
                    custom_coffee_menu.append(coffee_str)
                    custom_coffee_choices[i+1] = [coffee['name']]
                custom_coffee_menu = "\n".join(custom_coffee_menu)
                coffee = input_from_choice(f"{custom_coffee_menu}\nWhich custom coffee could you like to make: ",
                                           custom_coffee_choices)
                made_coffee(data["custom-coffee"][int(coffee)-1]["name"],
                            data["custom-coffee"][int(coffee)-1]["resources"],
                            data["resources"])


def refill_interface(data):
    needs_refill = []
    for r in RESOURCES:
        if data["resources"][r] < data["max"][r]:
            needs_refill.append(r)

    if not needs_refill:
        print("No need for a refill.")
    else:
        resource = input_from_choice("What would you like to refill: ",
                                     {"milk": "m", "water": "w", "coffee": "c", "back": "x"},
                                     help_msg=REFILL_HELP_MSG)
        if resource == "back":
            return
        if resource not in needs_refill:
            print(f"No need to refill {resource}")
        else:
            data["resources"][resource] = data["max"][resource]
            print(f"Successfully refilled {resource}")

def collect_interface(data):
    if data["resources"]['money'] != 0:
        print(f"${data['resources']['money'] / 100 :.2f} has been extracted from the machine")
        data['resources']['money'] = 0
    else:
        print("No money to extract.")

def ui():
    print(logo)
    time.sleep(2)
    os.system("cls")
    print("Welcome to the Coffee Machine Simulator!!!")
    data = get_data()

    try:
        while True:

            command = input_from_choice("Type command here: ",
                                        {0: ["order"], 1: ["report"], 2: ["refill"], 3: ["collect"], 4: ["off"]},
                                        help_msg=INTRO_HELP_MSG
                                        )

            os.system("cls")

            match int(command):
                case 0:
                    order_interface(data)
                case 1:
                    generate_report(data)
                case 2:
                    refill_interface(data)
                case 3:
                    collect_interface(data)
                case 4:
                    break
                case _:
                    print("Still working on it")
    except KeyboardInterrupt:
        pass
    finally:
        with open("bin/data-v1.json", "w") as file1:
            file1.write(json.dumps(data))
        print("Till next time!!!")


ui()
