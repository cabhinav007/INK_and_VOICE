import re

# Speech verbs and emotion trigger words
SPEECH_VERBS = {
    "said", "asked", "replied", "answered", "cried", "whispered", "shouted", 
    "yelled", "muttered", "murmured", "gasped", "sobbed", "wept", "screamed", 
    "snapped", "growled", "called", "demanded", "exclaimed", "sighed", "giggled", "laughed",
    "stammered", "stuttered", "pleaded", "begged", "declared", "announced", "responded",
    "insisted", "protested", "suggested", "admitted", "confessed", "warned", "urged",
    "grumbled", "groaned", "moaned", "chanted", "recited", "blurted", "interrupted"
}

EMOTION_TRIGGERS = {
    "sad": {"cried", "sobbed", "wept", "sighed", "sad", "sorrow", "tear", "gloom", "unhappy", "whimpered", "mourned", "grief", "pain", "suffering"},
    "joy": {"happy", "laughed", "smiled", "joy", "excited", "giggled", "cheerful", "glad", "delighted", "chuckled", "thrilled", "ecstatic", "beaming"},
    "angry": {"angry", "shouted", "yelled", "screamed", "furious", "harsh", "snapped", "growled", "raged", "scolded", "furiously", "angrily", "rage"}
}

# -----------------------------------------------------------------------
# Expanded name databases — includes Indian, Western, and global names
# -----------------------------------------------------------------------
FEMALE_NAMES = {
    # Western
    "mary", "sarah", "elizabeth", "emily", "jane", "lily", "lucy", "emma", "anna", "jessica",
    "sophia", "chloe", "olivia", "grace", "bella", "nicole", "ruth", "dorothy", "margaret", "helen",
    "alice", "clara", "charlotte", "diana", "eve", "fiona", "rose", "wendy", "daisy", "molly",
    "rachel", "rebecca", "laura", "kate", "catherine", "victoria", "caroline", "eleanor", "beatrice",
    "martha", "nancy", "susan", "linda", "patricia", "julia", "natalie", "sophie", "abigail",
    # Indian
    "meera", "devyani", "priya", "ananya", "kavya", "lakshmi", "radha", "sita", "gita", "padma",
    "deepa", "neha", "pooja", "shruti", "divya", "swati", "asha", "nandini", "savitri", "parvati",
    "gayatri", "rukmini", "saraswati", "durga", "kali", "uma", "leela", "kamala", "indira", "mala",
    "sunita", "anita", "rekha", "geeta", "usha", "suman", "renu", "seema", "jaya", "vijaya",
    "aishwarya", "rani", "devi", "maya", "tara", "anjali", "riya", "ishita", "aditi", "tanvi",
    "sneha", "pallavi", "rashmi", "shanti", "vani", "mythili", "bhavani", "revathi", "aruna",
    "chitra", "veena", "hema", "nisha", "sudha", "rama", "sarala", "vasundhara", "sarojini",
    # Global
    "fatima", "amara", "yuki", "sakura", "mei", "ling", "maria", "ana", "elena", "sofia",
    "aisha", "zara", "layla", "noor", "hana", "mina", "lina", "sara", "amina", "yasmin",
}

MALE_NAMES = {
    # Western
    "jack", "john", "peter", "david", "michael", "james", "robert", "william", "charles", "thomas",
    "arthur", "george", "lewis", "adam", "harry", "richard", "edward", "paul", "daniel", "matthew",
    "bob", "charlie", "henry", "oliver", "sam", "tom", "fred", "simon", "philip", "mark",
    "andrew", "stephen", "joseph", "benjamin", "alexander", "christopher", "nicholas", "patrick",
    "jonathan", "timothy", "brian", "kevin", "frank", "ralph", "gary", "roger", "dennis",
    # Indian
    "aarav", "arjun", "krishna", "ram", "shyam", "vikram", "raj", "rahul", "amit", "sunil",
    "mohan", "gopal", "ravi", "sanjay", "manoj", "anil", "vinod", "prakash", "suresh", "mahesh",
    "ganesh", "dinesh", "rajesh", "mukesh", "naresh", "ramesh", "kamal", "ashok", "vijay", "ajay",
    "deepak", "vivek", "anand", "rohan", "karan", "varun", "aditya", "dev", "harsh", "nikhil",
    "sachin", "kapil", "sourav", "virat", "rohit", "manish", "gaurav", "tushar", "pankaj",
    "bharat", "shiv", "shankar", "hari", "lakshman", "balram", "nakul", "aryan", "veer", "rudra",
    # Global
    "ahmed", "omar", "ali", "hassan", "hussein", "yusuf", "muhammad", "ibrahim", "ismail",
    "kai", "ryu", "hiroshi", "takeshi", "carlos", "diego", "pablo", "luis", "jose", "pedro",
}

# Name suffixes that strongly indicate gender
FEMALE_SUFFIXES = ("ini", "ani", "ika", "ita", "devi", "amma", "akka", "eera", "aya", "ya", "ia", "ie", "ine", "elle", "ette", "issa", "na")
MALE_SUFFIXES = ("esh", "esh", "raj", "ram", "dev", "man", "nath", "pal", "deep", "rav", "an", "ar")

# Common English words that start with a capital letter at the beginning of sentences (NOT names)
NON_NAME_WORDS = {
    # Pronouns & determiners
    "I", "He", "She", "It", "We", "They", "You", "Me", "Him", "Her", "Us", "My", "His",
    "Its", "Our", "Your", "Their", "This", "That", "These", "Those", "What", "Which",
    "Who", "Whom", "Whose", "Where", "When", "Why", "How", "Each", "Every", "Both",
    "All", "Some", "Any", "No", "None", "Few", "Many", "Much", "More", "Most", "Other",
    "Such", "Own", "Same",
    
    # Common verbs
    "Is", "Are", "Was", "Were", "Am", "Be", "Been", "Being", "Has", "Have", "Had",
    "Do", "Does", "Did", "Will", "Would", "Shall", "Should", "May", "Might", "Must",
    "Can", "Could", "Need", "Dare", "Get", "Got", "Gets", "Let", "Make", "Makes",
    "Made", "Come", "Comes", "Came", "Go", "Goes", "Went", "Gone", "Take", "Takes",
    "Took", "Give", "Gives", "Gave", "See", "Sees", "Saw", "Seen", "Know", "Knows",
    "Knew", "Known", "Think", "Thinks", "Thought", "Want", "Wants", "Wanted",
    "Look", "Looks", "Looked", "Looking", "Feel", "Feels", "Felt", "Find", "Finds",
    "Found", "Tell", "Tells", "Told", "Say", "Says", "Said", "Ask", "Asks", "Asked",
    "Try", "Tries", "Tried", "Leave", "Leaves", "Left", "Keep", "Keeps", "Kept",
    "Call", "Calls", "Called", "Turn", "Turns", "Turned", "Start", "Starts", "Started",
    "Show", "Shows", "Showed", "Run", "Runs", "Ran", "Move", "Moves", "Moved",
    "Live", "Lives", "Lived", "Believe", "Believes", "Believed", "Hold", "Holds", "Held",
    "Bring", "Brings", "Brought", "Happen", "Happens", "Happened", "Write", "Writes",
    "Sit", "Sits", "Sat", "Stand", "Stands", "Stood", "Lose", "Loses", "Lost",
    "Pay", "Pays", "Paid", "Meet", "Meets", "Met", "Play", "Plays", "Played",
    "Wait", "Waits", "Waited", "Waiting", "Stop", "Stops", "Stopped",
    "Open", "Opens", "Opened", "Walk", "Walks", "Walked", "Walking",
    "Read", "Reads", "Hear", "Hears", "Heard", "Speak", "Speaks", "Spoke",
    "Seem", "Seems", "Seemed", "Understand", "Understands", "Understood",
    "Watch", "Watches", "Watched", "Follow", "Follows", "Followed",
    "Die", "Dies", "Died", "Reach", "Reaches", "Reached",
    "Remember", "Remembers", "Remembered", "Consider", "Considers", "Considered",
    "Appear", "Appears", "Appeared", "Love", "Loves", "Loved", "Cry", "Cries", "Cried",
    "Smile", "Smiles", "Smiled", "Laugh", "Laughs", "Laughed", "Pull", "Pulls", "Pulled",
    "Push", "Pushes", "Pushed", "Catch", "Catches", "Caught",
    
    # Common adjectives / adverbs
    "Just", "Even", "Also", "Still", "Already", "Always", "Never", "Often", "Only",
    "Very", "Too", "Quite", "Rather", "Really", "Suddenly", "Slowly", "Quickly",
    "Finally", "Perhaps", "Maybe", "Probably", "Certainly", "Surely", "Actually",
    "Obviously", "Clearly", "Apparently", "Anyway", "However", "Nevertheless",
    "Meanwhile", "Otherwise", "Instead", "Besides", "Furthermore", "Moreover",
    "Therefore", "Thus", "Hence", "Consequently", "Accordingly",
    "Great", "Good", "Bad", "Long", "Short", "Big", "Small", "Old", "New", "Young",
    "Little", "Large", "High", "Low", "True", "Right", "Wrong", "Dark", "Light",
    "Hard", "Soft", "Strong", "Weak", "Deep", "Wide", "Tall", "Poor", "Rich",
    
    # Conjunctions / prepositions / articles
    "And", "But", "Or", "Nor", "For", "Yet", "So", "The", "A", "An",
    "In", "On", "At", "To", "From", "By", "With", "About", "Into", "Through",
    "During", "Before", "After", "Above", "Below", "Between", "Under", "Over",
    "Up", "Down", "Out", "Off", "Away", "Back", "Again", "Once", "Twice",
    "Here", "There", "Now", "Then", "Not", "If", "Because", "Since", "While",
    "Although", "Though", "Until", "Unless", "Whether", "Whenever", "Wherever",
    "Whatever", "Whoever", "However",
    
    # Time / place words
    "Today", "Tomorrow", "Yesterday", "Tonight", "Morning", "Evening", "Night",
    "Day", "Week", "Month", "Year", "Time", "Home", "House", "Room", "Door",
    "Way", "Place", "World", "Life", "Hand", "Head", "Eye", "Eyes", "Face",
    "Heart", "Mind", "Body", "Voice", "Word", "Words", "Man", "Woman",
    "People", "Children", "Child", "Boy", "Girl", "Mother", "Father",
    
    # Numbers / misc
    "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "First", "Second", "Third", "Last", "Next", "Half", "Several", "Enough",
    "Everything", "Something", "Nothing", "Anything", "Everyone", "Someone",
    "No one", "Nobody", "Somebody", "Everybody",
    
    # Narrative markers
    "Narrator", "Chapter", "Part", "Book", "End", "Prologue", "Epilogue",
    "Dear", "Well", "Oh", "Yes", "Okay", "Ah", "Hmm", "Uh", "Ok",
}

# ---------------------------------------------------------------------------
# Kokoro configuration & URLs
# ---------------------------------------------------------------------------
VCTK_SPEAKERS = {
    "Female": {
        "Young": [
            {"id": "bf_emma", "label": "Emma (Young, UK)"},
            {"id": "bf_isabella", "label": "Isabella (Young, UK)"},
            {"id": "af_bella", "label": "Bella (Soft, US)"},
        ],
        "Mid-Age": [
            {"id": "af_nicole", "label": "Nicole (Clear, US)"},
            {"id": "af_sarah", "label": "Sarah (Warm, US)"},
            {"id": "af_sky", "label": "Sky (Crisp, US)"},
            {"id": "af_heart", "label": "Heart (Expressive, US)"},
            {"id": "af_alloy", "label": "Alloy (Neutral, US)"},
            {"id": "af_jessica", "label": "Jessica (Bright, US)"},
            {"id": "af_kore", "label": "Kore (Gentle, US)"},
            {"id": "af_nova", "label": "Nova (Energetic, US)"},
            {"id": "af_river", "label": "River (Smooth, US)"},
        ],
        "Senior": [
            {"id": "af_sarah", "label": "Margaret (Mature, US)"},
            {"id": "bf_isabella", "label": "Dorothy (Seasoned, UK)"},
        ],
    },
    "Male": {
        "Young": [
            {"id": "am_puck", "label": "Puck (Young, US)"},
            {"id": "bm_lewis", "label": "Lewis (Young, UK)"},
        ],
        "Mid-Age": [
            {"id": "am_adam", "label": "Adam (Deep, US)"},
            {"id": "am_michael", "label": "Michael (Smooth, US)"},
            {"id": "bm_george", "label": "George (Polished, UK)"},
            {"id": "bm_daniel", "label": "Daniel (Conversational, UK)"},
            {"id": "am_fenrir", "label": "Fenrir (Strong, US)"},
            {"id": "bm_fable", "label": "Fable (Measured, UK)"},
        ],
        "Senior": [
            {"id": "am_adam", "label": "Arthur (Mature, US)"},
            {"id": "bm_george", "label": "Edward (Seasoned, UK)"},
        ],
    },
}

ALL_KOKORO_VOICES = {
    "af_nicole", "af_sarah", "af_bella", "af_sky", "af_heart", 
    "af_alloy", "af_jessica", "af_kore", "af_nova", "af_river",
    "bf_emma", "bf_isabella",
    "am_adam", "am_michael", "am_fenrir", "am_puck",
    "bm_george", "bm_lewis", "bm_daniel", "bm_fable"
}

KOKORO_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx"
KOKORO_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

PIPER_BINARY_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
VCTK_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx"
VCTK_CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx.json"
