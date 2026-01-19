document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM fully loaded, running loadLocations...");
    loadLocations();
    setupTabs();
    setupModals();
});

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');

            // Remove active class from all buttons and panes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked button and target pane
            btn.classList.add('active');
            const targetPane = document.getElementById(`${tabId}-tab`);
            if (targetPane) targetPane.classList.add('active');

            if (tabId === 'map' && window.map) {
                setTimeout(() => window.map.invalidateSize(), 100);
            }
        });
    });
}

function setupModals() {
    // Close modals when clicking X
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.onclick = function () {
            closeBtn.closest('.modal').style.display = "none";
        };
    });

    // Close modals when clicking outside
    window.onclick = function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    };
}

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
document.addEventListener("DOMContentLoaded", function () {
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
            total_sqft: sqft,
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

                    // Show save favorite button
                    const saveBtn = document.getElementById("saveFavoriteBtn");
                    if (saveBtn) saveBtn.classList.remove("hidden");
                } else {
                    priceOutput.innerHTML = "<h2 style='color:red;'>Error: No price received.</h2>";
                    document.getElementById("saveFavoriteBtn")?.classList.add("hidden");
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
        return;
    }

    let nearbyList = document.getElementById("nearbyList");
    if (!nearbyList) {
        console.error("nearbyList element not found!");
        return;
    }

    nearbyList.innerHTML = `<div class="loader-container"><div class="loader"></div><p>Searching for nearby ${type}s...</p></div>`;
    console.log(`Fetching nearby ${type} at coordinates:`, window.userLat, window.userLon);

    try {
        const response = await fetch(`/get_nearby_places?lat=${window.userLat}&lon=${window.userLon}&type=${type}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        console.log("Nearby Places Data:", data);

        // Clear existing markers
        if (window.amenityMarkers && window.amenityMarkers.length > 0) {
            window.amenityMarkers.forEach(marker => window.map.removeLayer(marker));
            window.amenityMarkers = [];
        }

        if (!data.places || data.places.length === 0) {
            nearbyList.innerHTML = `<div class="no-results"><i class="fas fa-info-circle"></i> No nearby ${type}s found within the search area.</div>`;
            return;
        }

        // Add new markers and populate list
        let placesHtml = '';
        data.places.forEach(place => {
            // Create marker
            const marker = L.marker([place.lat, place.lon]).addTo(window.map)
                .bindPopup(`<b>${place.name}</b><br>${place.distance_m ? Math.round(place.distance_m) + ' m away' : ''}`);
            window.amenityMarkers.push(marker);

            // Build card HTML
            placesHtml += `
                <div class="place-card" onclick="window.map.setView([${place.lat}, ${place.lon}], 16); window.amenityMarkers[${window.amenityMarkers.length - 1}].openPopup();">
                    <div class="place-info">
                        <div class="place-name">${place.name}</div>
                        <div class="place-type">${place.type}</div>
                    </div>
                    ${place.distance_m ? `<div class="place-distance"><i class="fas fa-walking"></i> ${Math.round(place.distance_m)}m</div>` : ''}
                </div>
            `;
        });

        nearbyList.innerHTML = placesHtml;

    } catch (error) {
        console.error("Error fetching places:", error);
        nearbyList.innerHTML = `<div class="error-msg">⚠️ Error fetching nearby ${type}: ${error.message}</div>`;
    }
}


// Save Favorite Properties
// Save Favorite Properties
function saveFavorite() {
    let location = document.getElementById("uiLocations").value;
    let sqft = document.getElementById("uiSqft").value;
    let bhk = document.querySelector("input[name='uiBHK']:checked")?.value;
    let bath = document.querySelector("input[name='uiBathrooms']:checked")?.value;
    let propertyAge = document.getElementById("uiPropertyAge")?.value;
    let priceElement = document.querySelector("#uiEstimatedPrice h2");

    if (!priceElement || priceElement.innerText === "") {
        alert("Estimate the price first before saving.");
        return;
    }

    // Extract numeric price
    let priceText = priceElement.innerText;
    let price = priceText.replace(/[^\d.]/g, ''); // Remove non-numeric chars except dot

    if (!location || location === "Choose a Location" || !sqft || !bhk || !bath || !propertyAge) {
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
            propertyAge: parseInt(propertyAge),
            price: parseFloat(price)
        })
    })
        .then(async response => {
            if (!response.ok) {
                // Check if it's a 401/403 (Unauthorized)
                if (response.status === 401 || response.status === 403) {
                    alert("Please log in to save properties.");
                    document.getElementById('authModal').style.display = 'block';
                    throw new Error("Unauthorized");
                }
                const err = await response.json();
                throw new Error(err.error || "Failed to save");
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadFavorites();
        })
        .catch(error => {
            console.error("Error saving favorite:", error);
        });
}


// Load Favorites with Card UI
function loadFavorites() {
    fetch("/get_favorites")
        .then(response => response.json())
        .then(data => {
            let favoritesList = document.getElementById("favoritesList");
            favoritesList.innerHTML = "";

            if (!data.favorites || data.favorites.length === 0) {
                favoritesList.innerHTML = "<p class='placeholder-text'>No saved properties found. Start by estimating a price!</p>";
                return;
            }

            // Store favorites globally for easy access during comparison
            window.allFavorites = data.favorites;

            data.favorites.forEach(fav => {
                let favItem = document.createElement("div");
                favItem.classList.add("favorite-card");

                // Store full data object as a string for easy retrieval
                favItem.dataset.details = JSON.stringify(fav);

                favItem.innerHTML = `
                    <div class="fav-check-wrapper">
                        <input type="checkbox" class="compare-checkbox" value="${fav.id}">
                    </div>
                    <button class="remove-fav-btn" onclick="deleteFavorite(${fav.id})" title="Remove">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                    <div class="fav-content">
                        <div class="fav-location">${fav.location}</div>
                        <div class="fav-details">
                            <span><i class="fas fa-bed"></i> ${fav.bhk} BHK</span> &bull; 
                            <span><i class="fas fa-bath"></i> ${fav.bath} Bath</span> &bull; 
                            <span><i class="fas fa-ruler-combined"></i> ${fav.sqft} sqft</span>
                        </div>
                        <div class="fav-details">
                            <span><i class="fas fa-calendar-alt"></i> ${fav.property_age} Years Old</span>
                        </div>
                        <div class="fav-price">₹${fav.price} Lakh</div>
                    </div>
                `;

                favoritesList.appendChild(favItem);
            });
        })
        .catch(error => console.error("Error loading favorites:", error));
}

// Compare Properties Logic
function compareProperties() {
    // Get all checked boxes
    const checkboxes = document.querySelectorAll('.compare-checkbox:checked');

    if (checkboxes.length < 2) {
        alert("Please select at least 2 properties to compare.");
        return;
    }

    if (checkboxes.length > 4) {
        alert("You can compare up to 4 properties at a time.");
        return;
    }

    // Collect data for selected properties
    let selectedProps = [];
    checkboxes.forEach(cb => {
        // Find the full favorite object from the global array
        const favId = parseInt(cb.value);
        const prop = window.allFavorites.find(f => f.id === favId);
        if (prop) selectedProps.push(prop);
    });

    // Calculate Price per Sqft for each and find "Best Value"
    let minPricePerSqft = Infinity;
    let bestValueIndex = -1;

    selectedProps.forEach((p, index) => {
        // Price is in Lakhs, Sqft is in units. 
        // Metric: Price (Lakhs) / Sqft * 100000 = Price per Sqft in Rupees
        // But for comparison, just Price/Sqft is enough.
        const pPerSqft = p.price / p.sqft;
        p.pricePerSqft = (pPerSqft * 100000).toFixed(0); // ₹/sqft

        if (pPerSqft < minPricePerSqft) {
            minPricePerSqft = pPerSqft;
            bestValueIndex = index;
        }
    });

    // Generate Table HTML
    let tableHtml = `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Feature</th>
                    ${selectedProps.map(p => `<th>${p.location}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Price</strong></td>
                    ${selectedProps.map(p => `<td><strong>₹${p.price} L</strong></td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Area (Sqft)</strong></td>
                    ${selectedProps.map(p => `<td>${p.sqft}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Price / Sqft</strong></td>
                    ${selectedProps.map((p, i) => {
        const isBest = i === bestValueIndex;
        return `<td class="${isBest ? 'best-value' : ''}">₹${p.pricePerSqft} ${isBest ? '' : ''}</td>`;
    }).join('')}
                </tr>
                <tr>
                    <td><strong>BHK</strong></td>
                    ${selectedProps.map(p => `<td>${p.bhk}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Bathrooms</strong></td>
                    ${selectedProps.map(p => `<td>${p.bath}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Age</strong></td>
                    ${selectedProps.map(p => `<td>${p.property_age} Years</td>`).join('')}
                </tr>
            </tbody>
        </table>
    `;

    // Inject into Modal
    document.getElementById('comparisonContainer').innerHTML = tableHtml;

    // Show Modal
    const modal = document.getElementById('compareModal');
    modal.style.display = "block";

    // Close Modal Logic
    modal.querySelector('.close').onclick = function () {
        modal.style.display = "none";
    }

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}

function updateMapLocation() {
    let locationDropdown = document.getElementById("uiLocations");
    let selectedLocation = locationDropdown.value;

    if (!selectedLocation) {
        console.error("❌ No location selected!");
        return;
    }

    console.log("📌 Fetching coordinates for:", selectedLocation);

    // Clear any existing amenity markers when location changes
    if (window.amenityMarkers) {
        window.amenityMarkers.forEach(marker => marker.remove());
        window.amenityMarkers = [];
    }

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

            // Update global user location (using window to ensure global scope)
            window.userLat = lat;
            window.userLon = lon;

            console.log(`✅ Map updated to: ${lat}, ${lon}`);

            // Remove old marker if exists
            if (window.currentMarker) {
                map.removeLayer(window.currentMarker);
            }

            // Add new marker
            window.currentMarker = L.marker([lat, lon]).addTo(map)
                .bindPopup(`<b>${selectedLocation}</b>`)
                .openPopup();

            // Move the map to new location
            map.setView([lat, lon], 14);

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

