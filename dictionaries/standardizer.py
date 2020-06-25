import usaddress
import string
from constants import (
    DIRECTIONAL_ABBREVIATIONS,
    STATE_ABBREVIATIONS,
    STREET_NAME_ABBREVIATIONS,
    STREET_NAME_POST_ABBREVIATIONS,
    OCCUPANCY_TYPE_ABBREVIATIONS,
    STREET_TYPE_CODES,
    DIRECTION_CODES
)
import number_processing
import re
# from number_processing import number_system, word


# USADDRESS CATEGORIES THAT WE ARE CONCERNED WITH
# AddressNumberPrefix
# AddressNumber
# AddressNumberSuffix
# StreetNamePreModifier
# StreetNamePreDirectional
# StreetNamePreType
# StreetName
# StreetNamePostType
# StreetNamePostDirectional
# SubaddressType
# SubaddressIdentifier
# BuildingName?


def abbreviate(potential_key, dictionary):
    if potential_key in dictionary:
        return dictionary.get(potential_key)
    else:
        return potential_key

# built for usaddress.tag, not usaddress.parse
# very preliminary, can be improved; let's talk about if we should parse replacements outside of specific labels
# applies abbreviate to each word parsed by usaddress

# input: parsed_address - output from usaddress.parse, in format Dict[(word, label)]
#        master_dict - a dict of functions, in format Dict[label, function], for processing terms
# output: a parsed address with words substituted when possible, in format List[(substitution, label)]
# List[(String, String)], Dict[String, Dict[String, String]] -> List[(String, String)] 
# def clean(parsed_address, master_dict):
#     return [(abbreviate(word, master_dict.get(label)), label) if label in master_dict else (word, label) for (word, label) in parsed_address]

# input: tagged_address - output from usaddress.tag, in format Dict[(words, label)]

def clean(tagged_address, master_dict):
    cleaned = {}
    for (label, words) in tagged_address.items():
        if label in master_dict:
            cleaned[label] = master_dict[label](words)
            # apply to full phrase (e.g. "country road", "one hundred and one")
            # result = master_dict[label](words)
            # if result != words:
            #     cleaned[label] = master_dict[label](words)
            #     result
            # # apply to each word individually
            # else:
            #     cleaned[label] = " ".join([master_dict[label](word) for word in words.split(" ")])
        else:
            cleaned[label] = words
    return cleaned
    # [(master_dict[label](word), label) if label in master_dict else (word, label) for (word, label) in parsed_address]
# TODO: implement processing between single-word and full-phrase

# examples: "one hundred eighty first", "vermont", "one hundred eighty fouth washington street"


# TODO: change to a map from label to individualized function (?)
label_dict = {
    'StreetNamePostType' : STREET_NAME_POST_ABBREVIATIONS,
    'StreetNamePreType' : STREET_NAME_POST_ABBREVIATIONS,
    'StreetNamePreDirectional' : DIRECTIONAL_ABBREVIATIONS,
    'StreetNamePostDirectional' : DIRECTIONAL_ABBREVIATIONS,
    'StateName' : STATE_ABBREVIATIONS,
    'SubaddressType' : OCCUPANCY_TYPE_ABBREVIATIONS,
    'StreetName' : STATE_ABBREVIATIONS # not sure if we want this for only StreetName; should "Washington Heights" in NYC become "WA HTS"?
}
# not sure what category street name substitutions fall under

# substitution codes
code_dict = {
    'StreetNamePostDirectional' : DIRECTION_CODES,
    'StreetNamePreDirectional' : DIRECTION_CODES,
    'StreetNamePostType' : STREET_TYPE_CODES,
    'StreetNamePreType' : STREET_TYPE_CODES
}

code_label_dict = {
    'StreetNamePostDirectional' : 'PostDirectionalCode',
    'StreetNamePreDirectional' : 'PreDirectionalCode',
    'StreetNamePostType' : 'SteetPostTypeCode',
    'StreetNamePreType' : 'SteetPreTypeCode'
}

"""
standardizes and replaces the following patterns:
    - state name to state abbreviations ("CALIFORNIA" -> "CA")
  if output = "number":
    - number words to numbers ("TWENTY THREE" -> "23")
      - handles hyphens, "and" ("ONE-HUNDRED-THREE", "ONE HUNDRED AND THREE")
      - handles ordinal words ("FORTY-FIFTH" -> "45")
    - ordinal number endings ("23RD" -> "23")
  if output = "word":
    - numbers to number words ("23" -> "TWENTY THREE")
      - handles ordinals ("23RD" -> "TWENTY THREE")
input: words, a string separated by spaces representing a street's name, uppercased
       ordinal, a boolean (default False) indicating if outputs are numerical ordinals
       output, either "number" (default) or "word" (indicating output format)
output: the same string, with relevant substitutions made
"""
# add options: raw numericals, numericals w/ ordinal endings, words, etc.
# port to preprocessing before standardizer (?); isolate
# -- make into a new(?) package / file, callable outside of usaddress
def street_process(words, ordinal = False, output = "number"):
    processed = []
    # terms = words.split()
    terms = re.split('-|\s',words)
    number_words = ""
    for word in terms:
        # check for number words if desired
        # needs to be updated to handle hyphens(?)
        if output = "number" and (word in number_processing.number_system or word == "and"):
            number_words = number_words + " " + word
            
        else:
            # replace any possible abbreviations first; join unreplaced chunks together
            # can eventually make a more general "common abbreviations dict" if we want ?
            if number_words:
                processed.append(str(number_processing.word_to_number(number_words, ordinal)))
                number_words = ""

            # PROCESS NON-NUMERIC WORDS HERE
            # if abbreviations give you numerical results this will have to be changed
            word = abbreviate(word, STATE_ABBREVIATIONS)

            # turn "101st" to "101"
            ## BEWARE OF WORDS THAT CONTAIN NUMERIC CHARACTERS - ONLY THE NUMBER WILL REMAIN
            digits = "".join([d for d in word if d.isdigit()])
            if digits:
                # turn "101" to "one hundred one"
                if output = "word":
                    word = number_processing.number_to_word(digits, ordinal)
                elif not ordinal:
                    word = digits

            processed.append(word)
    if number_words:
        processed.append(str(number_processing.word_to_number(number_words)))
    return " ".join(processed).upper()



# function dict
processing_dict = {
    'StreetNamePostType' : (lambda x : abbreviate(x, STREET_NAME_POST_ABBREVIATIONS)),
    'StreetNamePreType' : (lambda x : abbreviate(x, STREET_NAME_POST_ABBREVIATIONS)),
    'StreetNamePreDirectional' : (lambda x : abbreviate(x, DIRECTIONAL_ABBREVIATIONS)),
    'StreetNamePostDirectional' : (lambda x : abbreviate(x, DIRECTIONAL_ABBREVIATIONS)),
    'StateName' : (lambda x : abbreviate(x, STATE_ABBREVIATIONS)),
    'SubaddressType' : (lambda x : abbreviate(x, OCCUPANCY_TYPE_ABBREVIATIONS)),
    'StreetName' : street_process
}


# label_mappings = {
#     'AddressNumberPrefix' : 'HNPRE',
#     'AddressNumber' : 'HN1', # requires parsing into HN2 and HNSEP
#     'AddressNumberSuffix' : 'HNSUF',
#     'StreetNamePreModifier' : 'OSN', # will concat w/ StreetName
#     'StreetNamePreDirectional' : 'SNPD',
#     'StreetNamePreType' : 'SNST',
#     'StreetName': 'OSN',
#     'StreetNamePostType' : 'SNST',
#     'StreetNamePostModifier' : 'SNE', # Not sure if this is the correct correspondence
#     'StreetNamePostDirectional' : 'SNSD',
#     'SubaddressType' : 'WSD',
#     'SubaddressIdentifier' : 'WSI',
#     'BuildingName' : 'SI',
#     'OccupancyType',
#     'OccupancyIdentifier',
#     'CornerOf',
#     'LandmarkName',
#     'PlaceName',
#     'StateName',
#     'ZipCode' : 'ZIP',
#     'USPSBoxType',
#     'USPSBoxID' : 'BXI',
#     'USPSBoxGroupType',
#     'USPSBoxGroupID',
#     'IntersectionSeparator',
#     'Recipient',
#     'NotAddress',
# }


"""
input: address, any given address
       code, which can be "a" (append), "r" (replace), or "n" (none)
     ### REMOVED ###    output, which can be "l" (list) or "d" (dictionary)
output: a list formatted like that of usaddress.parse, but with certain key words abbreviated and standardized
String -> Dict[label: String, word: String] ### REMOVED ### List[(word: String, label: String)]
"""
def standardize(address, code = "a"):
    if code not in ["a", "r", "n"]:
        raise InputError("code must be a (append), r (replace), or n (none)")
    # make case insensitive, apply usaddress parsing
    tagged = usaddress.tag(address.upper())
    tagged = tagged[0]
    # remove punctuation from results (not removed beforehand, as punctuation can affect parsing)
    stripped = {label: words.translate(str.maketrans('', '', string.punctuation)).strip() for (label, words) in tagged.items()}
    # apply replacements
    substituted = clean(stripped, processing_dict)
    # add codes for directions, extensions, etc.
    if code != "n":
        pairs = list(substituted.items())
        for (label, word) in pairs:
            # confirm label is substitutable
            if label in code_dict and label in code_label_dict:
                # confirm substitution is known
                if word in code_dict[label]:
                    # add to dictionary
                    substituted[code_label_dict[label]] = code_dict[label].get(word)
                    # remove original value if requested
                    if code == "r":
                        substituted.pop(label)
    return substituted

if __name__== '__main__':
    """
    condition allows for 'interactive' testing and development when not being used as a library
    
    None of this will be run when it is "imported" which is helpful/cleaner
    """
    #as a rule, try to avoid typing the same term over and over again, a standard input file helps with testing
    testDataPath = r'testData.txt' # stored in current dir, for reasons...
    with open(testDataPath, 'r') as temp:
        data = [x[:-1] for x in temp.readlines()] #no header, 1 line per input, remove newline character
    
    for item in data:
        print(standardize(item))
        
    print('\n\nDone!') #old habits die hard, helpful to know if something is hanging...

# print(standardize("Homer Spit Road, Homer, Arkansas 99603"))
# print(standardize("Lnlck Shopping Center, Anniston, AL 36201"))
# print(standardize("Center Ridge, AR 72027"))
# print(standardize("9878 North Metro Parkway East, Phoenix, AZ 85051"))
# print(standardize("2896 Fairfax Street, Denver, CO 80207"))
# print(standardize("Mesa Mall, Grand Junction, CO 81501"))
# print(standardize("168 Hillside Avenue, Hartford, CT 06106"))
# print(standardize("1025 Vermont Avenue Northwest, Washington, DC 20005"))
# print(standardize("697 North Dupont Boulevard, Milford, DE 19963"))
# print(standardize("1915 North Republic De Cuba Avenue, Tampa, FL 33602"))
# print(standardize("2406 North Slappey Boulevard, Albany, GA 31701"))
# print(standardize("98-1247 Kaahumanu, Aiea, HI 96701"))
# print(standardize("103 West Main, Ute, IA 51060"))
# print(standardize("335 Deinhard Lane, Mc Call, ID 83638"))
# print(standardize("8922 South 1/2 Greenwood Avenue, Chicago, IL 60619"))
# print(standardize("239 West Monroe Street, Decatur, IN 46733"))
# print(standardize("827 Frontage Road, Agra, KS 67621"))
# print(standardize("508 West 6th Street, Lexington, KY 40508"))
# print(standardize("5103 Hollywood Avenue, Shreveport, LA 71109"))
# print(standardize("79 Power Road, Westford, MA 01886"))
# print(standardize("5105 Berwyn Road, College Park, MD 20740"))
# print(standardize("47 Broad Street, Auburn, ME 04210"))
# print(standardize("470 South Street, Ortonville, MI 48462"))
# print(standardize("404 Wilson Avenue, Faribault, MN 55021"))
# print(standardize("5933 Mc Donnell Boulevard, Hazelwood, MO 63042"))
# print(standardize("918 East Main Avenue, Lumberton, MS 39455"))
# print(standardize("107 A Street East, Poplar, MT 59255"))
# print(standardize("Village Shps Of Bnr, Banner Elk, NC 28604"))
# print(standardize("2601 State Street, Bismarck, ND 58501"))
# print(standardize("207 South Bell Street, Fremont, NE 68025"))
# print(standardize("107 State Street, Portsmouth, NH 03801"))
# print(standardize("1413 State Highway #50, Mays Landing, NJ 08330"))
# print(standardize("I-25 Highway 87, Raton, NM 87740"))
# print(standardize("516 West Goldfield Avenue, Yerington, NV 89447"))
# print(standardize("2787 Bway Way, New York, NY 10001"))
# print(standardize("1380 Bethel Road, Columbus, OH 43220"))
# print(standardize("305 Main, Fort Cobb, OK 73038"))
# print(standardize("17375 Southwest Tualatin Valley Hwy, Beaverton, OR 97006"))