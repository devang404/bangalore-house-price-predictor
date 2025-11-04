document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM fully loaded, running loadLocations...");
    loadLocations();
});

// Function to load locations into the dropdown
window.loadLocations = async function (retryCount = 3) {
    console.log("✅ Fetching locations...");

    let locationDropdown = document.getElementById("uiLocations");
    if (!locationDropdown) {
        console.error("❌ Dropdown element NOT found!");
        alert("Dropdown not found in the HTML. Please check the ID!");
        return;
    }

    // Clear and set default option
    locationDropdown.innerHTML = "<option value='' disabled selected>Choose a Location</option>";

    while (retryCount > 0) {
        try {
            let response = await fetch("/get_locations");
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            let data = await response.json();
            console.log("📌 API Response:", data);

            if (data.locations && data.locations.length > 0) {
                data.locations.forEach(location => {
                    let option = document.createElement("option");
                    option.value = location;
                    option.textContent = location;
                    locationDropdown.appendChild(option);
                });

                console.log("✅ Dropdown Updated Successfully!");
                return; // Exit function after successful update
            } else {
                console.warn("⚠️ No locations received from API.");
                alert("No locations available. Please check the backend API!");
                return;
            }
        } catch (error) {
            console.error(`❌ Error fetching locations (Attempts left: ${retryCount - 1}):`, error);
            retryCount--;

            if (retryCount === 0) {
                alert("Error fetching locations after multiple attempts. Check the server!");
            }
        }
    }
};




<<<<<<< HEAD
// Initialize Leaflet Map
let map;
function initMap() {
    map = L.map('mapView').setView([12.9716, 77.5946], 14); // Default to Bangalore

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    L.marker([12.9716, 77.5946]).addTo(map)
        .bindPopup("Bangalore (Default Location)")
        .openPopup();
}
window.onload = initMap;
=======
// Initialize global variables
window.map = null;
window.currentMarker = null;
window.userLat = null;
window.userLon = null;
window.amenityMarkers = [];

// Initialize Leaflet Map
function initMap() {
    console.log("Initializing map...");
    const mapElement = document.getElementById('mapView');
    if (!mapElement) {
        console.error("Map container not found!");
        return;
    }

    try {
        // Initialize the map
        window.map = L.map('mapView').setView([12.9716, 77.5946], 14); // Default to Bangalore
        
        // Add the tile layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors"
        }).addTo(window.map);

        // Add default marker
        window.currentMarker = L.marker([12.9716, 77.5946])
            .addTo(window.map)
            .bindPopup("Bangalore (Default Location)")
            .openPopup();

        console.log("✅ Map initialized successfully!");
    } catch (error) {
        console.error("❌ Error initializing map:", error);
    }
}

// Wait for DOM and Leaflet to load
document.addEventListener("DOMContentLoaded", function() {
    if (typeof L !== 'undefined') {
        console.log("Leaflet is loaded, initializing map...");
        initMap();
    } else {
        console.error("Leaflet is not loaded!");
        // Wait a bit and try again
        setTimeout(() => {
            if (typeof L !== 'undefined') {
                console.log("Leaflet loaded after delay, initializing map...");
                initMap();
            } else {
                console.error("Failed to load Leaflet even after delay!");
            }
        }, 1000);
    }
});
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)


// Estimate Price
function estimatePrice() {
    // Get input values
    let location = document.getElementById("uiLocations")?.value;
    let sqft = parseFloat(document.getElementById("uiSqft")?.value);
    let bhk = document.querySelector('input[name="uiBHK"]:checked')?.value;
    let bath = document.querySelector('input[name="uiBathrooms"]:checked')?.value;
    let propertyAge = document.getElementById("uiPropertyAge")?.value;

    // Input validation
    if (!location || isNaN(sqft) || !bhk || !bath || !propertyAge) {
        alert("Please fill in all details before estimating the price.");
        return;
    }

    // Send request to backend
    fetch("/predict_price", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            location: location,
            total_sqft:sqft,
            bhk: parseInt(bhk),
            bath: parseInt(bath),
            property_age: parseInt(propertyAge),
        }),
    })
    .then(response => response.json())
    .then(data => {
        let priceOutput = document.getElementById("uiEstimatedPrice");
        if (priceOutput) {
            if (data.estimated_price !== undefined) {
                let finalPrice = Math.abs(data.estimated_price);
                priceOutput.innerHTML = `<h2>Estimated Price: ₹${finalPrice.toLocaleString()} Lakh</h2>`;
            } else {
                priceOutput.innerHTML = "<h2 style='color:red;'>Error: No price received.</h2>";
            }
        }
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("uiEstimatedPrice").innerHTML =
            "<h2 style='color:red;'>Error: Could not fetch prediction.</h2>";
    });
}


// Attach event listener to estimate button
document.addEventListener("DOMContentLoaded", function () {
    let estimateBtn = document.getElementById("estimateBtn");
    if (estimateBtn) {
        estimateBtn.addEventListener("click", estimatePrice);
    }
});

<<<<<<< HEAD
// Nearby Places API Call
let userLat, userLon;
let nearbyMarkers = [];  // Store markers to clear them later

async function fetchNearbyPlaces(type) {
    if (!userLat || !userLon) {
        alert("Select a location first!");
=======
// Amenity markers storage
window.amenityMarkers = [];  // Store markers to clear them later

// Nearby Places API Call
async function fetchNearbyPlaces(type) {
    console.log("fetchNearbyPlaces called with type:", type);
    
    // Check if map is initialized
    if (!window.map) {
        console.error("Map not initialized!");
        alert("Map is not ready. Please refresh the page and try again.");
        return;
    }

    // Check if location is selected
    if (!window.userLat || !window.userLon) {
        alert("Please select a location first!");
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)
        return;
    }

    let nearbyList = document.getElementById("nearbyList");
<<<<<<< HEAD
    nearbyList.innerHTML = `<p>Loading nearby ${type}...</p>`;

    try {
        let response = await fetch(`/get_nearby_places?lat=${userLat}&lon=${userLon}&type=${type}`);
        let data = await response.json();

        console.log("Nearby Places Data:", data);

        if (!data.places || data.places.length === 0) {
            nearbyList.innerHTML = `<p>No nearby ${type} found.</p>`;
            return;
        }

        // Clear existing markers before adding new ones
        nearbyMarkers.forEach(marker => marker.remove());
        nearbyMarkers = [];

        // Loop through places and add them as markers
        data.places.forEach(place => {
            let marker = L.marker([place.lat, place.lon])
                .addTo(map)  // Assuming you already have a `map` object
                .bindPopup(`<strong>${place.name}</strong><br>(${place.lat}, ${place.lon})`);

            nearbyMarkers.push(marker);  // Store markers for future removal
        });

        nearbyList.innerHTML = `<p>${data.places.length} nearby ${type} found and displayed on the map.</p>`;

    } catch (error) {
        console.error("Error fetching places:", error);
        nearbyList.innerHTML = "<p>Error fetching amenities.</p>";
=======
    if (!nearbyList) {
        console.error("nearbyList element not found!");
        return;
    }

    nearbyList.innerHTML = `<p>Loading nearby ${type}...</p>`;
    console.log(`Fetching nearby ${type} at coordinates:`, window.userLat, window.userLon);

    try {
        const response = await fetch(`/get_nearby_places?lat=${window.userLat}&lon=${window.userLon}&type=${type}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        console.log("Nearby Places Data:", data);

        // Clear existing markers
        if (window.amenityMarkers) {
            window.amenityMarkers.forEach(marker => marker.remove());
            window.amenityMarkers = [];
        }

        if (!data.places || data.places.length === 0) {
            nearbyList.innerHTML = `<p>No nearby ${type} found within range.</p>`;
            return;
        }

        // Add new markers
        data.places.forEach(place => {
  L.marker([place.lat, place.lon]).addTo(map)
    .bindPopup(`<b>${place.name}</b><br>${place.distance_m} m`);
});


        // Update list
        nearbyList.innerHTML = `
            <p>✅ Found ${data.places.length} nearby ${type}${data.places.length > 1 ? 's' : ''}</p>
            <ul>
                ${data.places.map(place => `
                    <li>
                        <strong>${place.name}</strong>
                        ${place.description ? `<br>${place.description}` : ''}
                        ${place.distance_m ? `<br><small>Distance: ${place.distance_m} m</small>` : ''}
                    </li>
                `).join('')}
            </ul>
        `;

    } catch (error) {
        console.error("Error fetching places:", error);
        nearbyList.innerHTML = `<p>⚠️ Error fetching nearby ${type}: ${error.message}</p>`;
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)
    }
}


// Save Favorite Properties
function saveFavorite() {
    let location = document.getElementById("uiLocations").value;
    let sqft = document.getElementById("uiSqft").value;
    let bhk = document.querySelector("input[name='uiBHK']:checked")?.value;
    let bath = document.querySelector("input[name='uiBathrooms']:checked")?.value;
    let priceElement = document.querySelector("#uiEstimatedPrice h2");

    if (!priceElement) {
        alert("Estimate the price first before saving.");
        return;
    }

    let price = priceElement.innerText.replace("Estimated Price: ₹", "").replace(" Lakh", "");

    if (!location || location === "Choose a Location" || !sqft || !bhk || !bath || !price) {
        alert("Please fill in all the required fields before saving.");
        return;
    }

    fetch("/save_favorite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            location: location,
            sqft: parseInt(sqft),
            bhk: parseInt(bhk),
            bath: parseInt(bath),
            propertyAge: Math.floor(Math.random() * 20) + 1, // Simulating property age
            price: parseFloat(price)
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadFavorites(); // Refresh the saved properties list
    })
    .catch(error => console.error("Error saving favorite:", error));
}


function loadFavorites() {
    fetch("/get_favorites")
        .then(response => response.json())
        .then(data => {
            let favoritesList = document.getElementById("favoritesList");
            favoritesList.innerHTML = ""; // Clear existing list

            if (!data.favorites || data.favorites.length === 0) {
                favoritesList.innerHTML = "<p>No saved properties found.</p>";
                return;
            }

            data.favorites.forEach(fav => {
                let favItem = document.createElement("div");
                favItem.classList.add("favorite-item");

                favItem.innerHTML = `
                    <strong>${fav.location}</strong> - ${fav.sqft} sqft, ${fav.bhk} BHK, ${fav.bath} Bath, ${fav.property_age} years old - ₹${fav.price}L
                    <button class="remove-fav" onclick="deleteFavorite(${fav.id})">❌ Remove</button>
                `;

                favoritesList.appendChild(favItem);
            });

            document.getElementById("savedPropertiesSection").style.display = "block"; // Show the saved properties section
        })
        .catch(error => console.error("Error loading favorites:", error));
}



// Delete Favorite
function deleteFavorite(favId) {
    fetch(`/delete_favorite/${favId}`, { method: "DELETE" })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadFavorites(); // Refresh the list after deletion
        })
        .catch(error => console.error("Error deleting favorite:", error));
}


// Compare Properties
document.getElementById("compareBtn").addEventListener("click", function () {
    let selectedProperties = document.querySelectorAll(".favorite-item input[type='checkbox']:checked");

    if (selectedProperties.length < 2) {
        alert("Select at least two properties to compare.");
        return;
    }

    let comparisonTable = "<table border='1'><tr><th>Location</th><th>Sqft</th><th>BHK</th><th>Bath</th><th>Price</th></tr>";
    selectedProperties.forEach(checkbox => {
        let details = checkbox.parentElement.dataset.details.split("|");
        comparisonTable += `<tr><td>${details.join("</td><td>")}</td></tr>`;
    });
    comparisonTable += "</table>";
    document.getElementById("comparisonResult").innerHTML = comparisonTable;
});

function updateMapLocation() {
    let locationDropdown = document.getElementById("uiLocations");
    let selectedLocation = locationDropdown.value;

    if (!selectedLocation) {
        console.error("❌ No location selected!");
        return;
    }

    console.log("📌 Fetching coordinates for:", selectedLocation);

<<<<<<< HEAD
=======
    // Clear any existing amenity markers when location changes
    if (window.amenityMarkers) {
        window.amenityMarkers.forEach(marker => marker.remove());
        window.amenityMarkers = [];
    }

>>>>>>> 6c254c7 (Updated project files and pushed recent changes)
    fetch(`/get_location_coords?location=${encodeURIComponent(selectedLocation)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("❌ Location not found:", data.error);
                alert("Location not found on map.");
                return;
            }

            let lat = parseFloat(data.lat);
            let lon = parseFloat(data.lon);

<<<<<<< HEAD
            // Update global user location
            userLat = lat;
            userLon = lon;
=======
            // Update global user location (using window to ensure global scope)
            window.userLat = lat;
            window.userLon = lon;
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)

            console.log(`✅ Map updated to: ${lat}, ${lon}`);

            // Remove old marker if exists
            if (window.currentMarker) {
<<<<<<< HEAD
                map.removeLayer(window.currentMarker);
            }

            // Add new marker
            window.currentMarker = L.marker([lat, lon]).addTo(map)
=======
                window.map.removeLayer(window.currentMarker);
            }

            // Add new marker
            window.currentMarker = L.marker([lat, lon]).addTo(window.map)
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)
                .bindPopup(`<b>${selectedLocation}</b>`)
                .openPopup();

            // Move the map to new location
<<<<<<< HEAD
            map.setView([lat, lon], 14);
        })
        .catch(error => console.error("❌ Error fetching location:", error));
=======
            window.map.setView([lat, lon], 14);

            // Clear the nearby list
            let nearbyList = document.getElementById("nearbyList");
            if (nearbyList) {
                nearbyList.innerHTML = '<p>Select an amenity type to see nearby places</p>';
            }
        })
        .catch(error => {
            console.error("❌ Error fetching location:", error);
            alert("Error updating location. Please try again.");
        });
>>>>>>> 6c254c7 (Updated project files and pushed recent changes)
}
window.addEventListener("DOMContentLoaded", function () {
    const slider = document.getElementById("uiPropertyAge");
    const output = document.getElementById("propertyAgeValue");

    if (slider && output) {
        // Set initial value
        output.innerText = slider.value;

        // Listen for slider movement
        slider.addEventListener("input", function () {
            output.innerText = this.value;
        });
    }
});

