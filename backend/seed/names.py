"""Realistic Indian names: mostly Telugu (hand-written lists), plus other regions from Faker."""
from seed.stories import ARJUN, KARTHIK, SNEHA

TELUGU_FIRST = [
    "Aditya", "Akhil", "Anusha", "Bhargav", "Chaitanya", "Deepika", "Divya", "Ganesh", "Harika", "Harsha",
    "Jyothi", "Kavya", "Kiran", "Lakshmi", "Lavanya", "Madhavi", "Mahesh", "Manasa", "Naveen", "Nikhil",
    "Padma", "Pavan", "Pranathi", "Praveen", "Rajesh", "Ramya", "Ravi", "Sai Kiran", "Sandeep", "Sirisha",
    "Sravani", "Srikanth", "Srinivas", "Suresh", "Swathi", "Tejaswi", "Uma", "Varun", "Venkat", "Vijay",
    "Vamsi", "Yamini", "Anil", "Bhavana", "Charan", "Gopi", "Hemanth", "Keerthi", "Mounika", "Rohith",
]
TELUGU_LAST = [
    "Reddy", "Rao", "Naidu", "Chowdary", "Goud", "Varma", "Sharma", "Murthy", "Prasad", "Yadav",
    "Kumar", "Raju", "Sastry", "Gupta", "Babu", "Chary", "Nayak", "Setty", "Patnaik", "Konda",
    "Vemula", "Bandaru", "Kolli", "Nalla", "Gadde", "Yerra", "Mandava", "Pulla", "Tummala", "Kancharla",
]
RESERVED = {KARTHIK, SNEHA, ARJUN}  # story characters; nobody else gets these names


def person(w, unique: bool = False) -> str:
    """About 70% Telugu names. `unique` is used for employees and customers."""
    while True:
        if w.rng.random() < 0.7:
            name = f"{w.rng.choice(TELUGU_FIRST)} {w.rng.choice(TELUGU_LAST)}"
        else:
            name = f"{w.fake.first_name()} {w.fake.last_name()}"
        if name in RESERVED or (unique and name in w.used_names):
            continue
        if unique:
            w.used_names.add(name)
        return name


def email_for(name: str, number: int, domain: str = "example.com") -> str:
    """example.com is reserved for examples, so these can never reach a real inbox."""
    return f"{name.lower().replace(' ', '.')}{number}@{domain}"
