from flask import Flask, render_template, request
import os
from rdflib import Graph, Namespace
from collections import defaultdict

app = Flask(__name__)

# Path to your ontology file
GRAPH_FILE = os.path.abspath("D:/TravelTripAdvisor/ontology/travel.ttl")

# Check if the ontology file exists
if not os.path.exists(GRAPH_FILE):
    raise FileNotFoundError(f"The ontology file was not found at: {GRAPH_FILE}")

# Namespace for the ontology
EX = Namespace("http://www.travel-advisor.org/ontology#")

# Load the TTL file into an RDFLib graph
g = Graph()
try:
    g.parse(GRAPH_FILE, format="turtle")
    print("Graph successfully parsed!")
except Exception as e:
    print("Error parsing graph:", e)


def query_local_ttl(profile):
    """
    Queries the ontology for destinations, activities, hotels, attraction,
    booking options, reviews, and maps based on the provided travel profile.
    """
    query = f"""
    PREFIX : <http://www.travel-advisor.org/ontology#>
    SELECT DISTINCT ?destination ?activity ?attraction ?hotel ?booking ?review ?map WHERE {{
        ?destination :suitableFor :{profile} .
        OPTIONAL {{ ?destination :hasActivity ?activity }} .
        OPTIONAL {{ ?destination :hasAttraction ?attraction }} .
        OPTIONAL {{ ?destination :hasHotel ?hotel }} .
        OPTIONAL {{ ?destination :hasBookingOption ?booking }} .
        OPTIONAL {{ ?destination :hasGoogleReview ?review }} .
        OPTIONAL {{ ?destination :hasLocationMap ?map }} .
    }}
    """

    try:
        results = g.query(query)
    except Exception as e:
        print(f"Error executing SPARQL query: {e}")
        return []

    # Group data by destination
    grouped_results = defaultdict(lambda: {"activities": set(), "hotels": set(), "attraction": set(), "booking": "", "review": "", "map": ""})

    for row in results:
        destination = str(row.destination).split("#")[1] if row.destination else "N/A"  # Extract the destination name
        grouped_results[destination]["activities"].add(str(row.activity).split("#")[1] if row.activity else "N/A")
        grouped_results[destination]["attraction"].add(str(row.attraction) if row.attraction else "N/A")
        grouped_results[destination]["hotels"].add(str(row.hotel).split("#")[1] if row.hotel else "N/A")
        grouped_results[destination]["booking"] = str(row.booking) if row.booking else "N/A"
        grouped_results[destination]["review"] = str(row.review) if row.review else "N/A"
        grouped_results[destination]["map"] = str(row.map) if row.map else "N/A"

    # Convert grouped results into a list of dictionaries for rendering
    results = [
        {
            "destination": destination,
            "activities": list(data["activities"]),
            "attraction": list(data["attraction"]),
            "hotels": list(data["hotels"]),
            "booking": data["booking"],
            "review": data["review"],
            "map": data["map"],
        }
        for destination, data in grouped_results.items()
    ]

    return results


@app.route("/search", methods=["GET"])
def search():
    """
    Handle the search functionality based on the selected profile.
    """
    profile = request.args.get("profile")  # Retrieve the selected profile (e.g., Solo, Family)
    if not profile:
        return "Error: No profile selected", 400

    # Query the ontology for travel data
    results = query_local_ttl(profile)

    # Pass the results list directly to the template
    return render_template("result.html", results=results)

@app.route("/destinations")
def destinations():
    """
    Render the Destinations page with a list of all destinations and their images.
    """
    query = """
    PREFIX : <http://www.travel-advisor.org/ontology#>
    SELECT DISTINCT ?destination ?map WHERE {
        ?destination rdf:type :Destination .
     
        OPTIONAL { ?destination :hasLocationMap ?map } .
        
    }
    """
    try:
        results = g.query(query)
    except Exception as e:
        print(f"Error executing SPARQL query: {e}")
        return "Error fetching destinations"

    # Convert results into a list of dictionaries
    destinations = [
        {
            "name": str(row.destination).split("#")[1] if row.destination else "N/A",
           
            "map": str(row.map) if row.map else "#"
        }
        for row in results
    ]

    print(destinations)  # Debugging output to check data
    return render_template("destinations.html", destinations=destinations)


def query_services():
    """
    Queries the ontology for services offered.
    """
    query = """
    PREFIX : <http://www.travel-advisor.org/ontology#>
    SELECT ?service ?label ?comment WHERE {
        ?service rdf:type :Service .
        ?service rdfs:label ?label .
        ?service rdfs:comment ?comment .
    }
    """

    try:
        results = g.query(query)
    except Exception as e:
        print(f"Error executing SPARQL query: {e}")
        return []

    # Convert results into a list of dictionaries
    services = [
        {
            "label": str(row.label),
            "comment": str(row.comment)
        }
        for row in results
    ]

    return services

@app.route("/")
def home():
    """
    Render the home page.
    """
    return render_template("index.html")  # Ensure this file exists in the templates folder

@app.route("/about")
def about():
    """
    Render the About page.
    """
    return render_template("about.html") 

@app.route("/services")
def services():
    """
    Render the Services page.
    """
    services = query_services()
    return render_template("service.html", services=services)


if __name__ == "__main__":
    app.run(debug=True)
