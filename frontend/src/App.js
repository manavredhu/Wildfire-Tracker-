import React, { useEffect, useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Leaflet marker fix (warna marker icon React Leaflet me dikhega nahi)
import L from "leaflet";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl,
  shadowUrl: iconShadow,
});
L.Marker.prototype.options.icon = DefaultIcon;

function App() {
  const [fires, setFires] = useState([]);

  useEffect(() => {
    // Backend se last 7 days ka global fire data fetch kar rahe hain
    axios
      .get("http://localhost:8000/fires/area", {
        params: {
          bbox: "-180,-90,180,90", // pura globe
          days: 7,                 // last 7 din
          source: "VIIRS_SNPP_NRT",// FIRMS satellite data source
          limit: 2000,             // max records (performance ke liye control)
        },
      })
      .then((res) => {
        setFires(res.data.fires || []);
      })
      .catch((err) => {
        console.error("Error fetching fire data:", err);
      });
  }, []);

  return (
    <div>
      <h1>🌍 Global Wildfire Tracker (Last 7 Days)</h1>
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: "90vh", width: "100%" }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        
        {fires.map((fire, index) => (
          <Marker key={index} position={[fire.latitude, fire.longitude]}>
            <Popup>
              <b>🔥 Fire Detected</b><br />
              Date: {fire.acq_date}<br />
              Time: {fire.acq_time}<br />
              Confidence: {fire.confidence}<br />
              Brightness: {fire.bright_ti4}<br />
              FRP: {fire.frp}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

export default App;