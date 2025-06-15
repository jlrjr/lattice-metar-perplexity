import plotly.graph_objects as go
import plotly.io as pio

# Create a technical architecture diagram as a flowchart
fig = go.Figure()

# Define positions for components (x, y coordinates)
# Data Sources (left side)
faa_api_pos = (1, 8)
metar_endpoints_pos = (1, 7)
taf_endpoints_pos = (1, 6)

# Processing Components (center-left)
metar_client_pos = (3.5, 7.5)
parsing_pos = (3.5, 6.5)
classification_pos = (3.5, 5.5)
airports_db_pos = (3.5, 4.5)

# Integration Layer (center-right)
integration_pos = (6, 6)
entity_creation_pos = (6, 5)
grpc_client_pos = (6, 4)

# Lattice Platform (right side)
entity_manager_pos = (8.5, 6)
weather_entities_pos = (8.5, 5)
monitoring_pos = (8.5, 4)

# Define component boxes with colors from brand palette
components = [
    # Data Sources (Strong cyan)
    {"name": "FAA Weather API", "pos": faa_api_pos, "color": "#1FB8CD", "width": 1.2, "height": 0.6},
    {"name": "METAR Endpoints", "pos": metar_endpoints_pos, "color": "#1FB8CD", "width": 1.2, "height": 0.5},
    {"name": "TAF Endpoints", "pos": taf_endpoints_pos, "color": "#1FB8CD", "width": 1.2, "height": 0.5},
    
    # Processing Components (Light orange)
    {"name": "MetarApiClient", "pos": metar_client_pos, "color": "#FFC185", "width": 1.3, "height": 0.5},
    {"name": "METAR Parsing", "pos": parsing_pos, "color": "#FFC185", "width": 1.3, "height": 0.5},
    {"name": "Flight Condition", "pos": classification_pos, "color": "#FFC185", "width": 1.3, "height": 0.5},
    {"name": "19+ Airports DB", "pos": airports_db_pos, "color": "#FFC185", "width": 1.3, "height": 0.5},
    
    # Integration Layer (Light green)
    {"name": "Weather Intgr", "pos": integration_pos, "color": "#ECEBD5", "width": 1.3, "height": 0.5},
    {"name": "Entity Creation", "pos": entity_creation_pos, "color": "#ECEBD5", "width": 1.3, "height": 0.5},
    {"name": "gRPC Client", "pos": grpc_client_pos, "color": "#ECEBD5", "width": 1.3, "height": 0.5},
    
    # Lattice Platform (Cyan)
    {"name": "Entity Mgr API", "pos": entity_manager_pos, "color": "#5D878F", "width": 1.3, "height": 0.5},
    {"name": "Weather Sensors", "pos": weather_entities_pos, "color": "#5D878F", "width": 1.3, "height": 0.5},
    {"name": "Real-time Mon", "pos": monitoring_pos, "color": "#5D878F", "width": 1.3, "height": 0.5},
]

# Add component boxes
for comp in components:
    x, y = comp["pos"]
    w, h = comp["width"], comp["height"]
    
    # Add rectangle
    fig.add_shape(
        type="rect",
        x0=x-w/2, y0=y-h/2, x1=x+w/2, y1=y+h/2,
        fillcolor=comp["color"],
        line=dict(color="black", width=1),
        opacity=0.8
    )
    
    # Add text
    fig.add_annotation(
        x=x, y=y,
        text=comp["name"],
        showarrow=False,
        font=dict(size=10, color="black"),
        xanchor="center",
        yanchor="middle"
    )

# Define arrows for data flow
arrows = [
    # From FAA API to processing
    {"start": (faa_api_pos[0]+0.6, faa_api_pos[1]), "end": (metar_client_pos[0]-0.65, metar_client_pos[1]+0.2), "label": "HTTP REST"},
    {"start": (metar_endpoints_pos[0]+0.6, metar_endpoints_pos[1]), "end": (metar_client_pos[0]-0.65, metar_client_pos[1]), "label": "JSON/XML"},
    {"start": (taf_endpoints_pos[0]+0.6, taf_endpoints_pos[1]), "end": (metar_client_pos[0]-0.65, metar_client_pos[1]-0.2), "label": ""},
    
    # Processing flow
    {"start": (metar_client_pos[0], metar_client_pos[1]-0.25), "end": (parsing_pos[0], parsing_pos[1]+0.25), "label": ""},
    {"start": (parsing_pos[0], parsing_pos[1]-0.25), "end": (classification_pos[0], classification_pos[1]+0.25), "label": "VFR/IFR"},
    {"start": (classification_pos[0], classification_pos[1]-0.25), "end": (airports_db_pos[0], airports_db_pos[1]+0.25), "label": ""},
    
    # To integration layer
    {"start": (metar_client_pos[0]+0.65, metar_client_pos[1]), "end": (integration_pos[0]-0.65, integration_pos[1]+0.3), "label": ""},
    {"start": (classification_pos[0]+0.65, classification_pos[1]), "end": (integration_pos[0]-0.65, integration_pos[1]-0.3), "label": "30min cycle"},
    
    # Integration flow
    {"start": (integration_pos[0], integration_pos[1]-0.25), "end": (entity_creation_pos[0], entity_creation_pos[1]+0.25), "label": ""},
    {"start": (entity_creation_pos[0], entity_creation_pos[1]-0.25), "end": (grpc_client_pos[0], grpc_client_pos[1]+0.25), "label": ""},
    
    # To Lattice
    {"start": (grpc_client_pos[0]+0.65, grpc_client_pos[1]), "end": (entity_manager_pos[0]-0.65, entity_manager_pos[1]+0.3), "label": "gRPC"},
    {"start": (entity_manager_pos[0], entity_manager_pos[1]-0.25), "end": (weather_entities_pos[0], weather_entities_pos[1]+0.25), "label": ""},
    {"start": (weather_entities_pos[0], weather_entities_pos[1]-0.25), "end": (monitoring_pos[0], monitoring_pos[1]+0.25), "label": ""},
]

# Add arrows
for arrow in arrows:
    start_x, start_y = arrow["start"]
    end_x, end_y = arrow["end"]
    
    # Add arrow
    fig.add_annotation(
        x=end_x, y=end_y,
        ax=start_x, ay=start_y,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        axref="x", ayref="y"
    )
    
    # Add label if provided
    if arrow["label"]:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        fig.add_annotation(
            x=mid_x, y=mid_y + 0.1,
            text=arrow["label"],
            showarrow=False,
            font=dict(size=8, color="black"),
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        )

# Add section headers
fig.add_annotation(
    x=1, y=9,
    text="Data Sources",
    showarrow=False,
    font=dict(size=12, color="black", family="Arial Black"),
    xanchor="center"
)

fig.add_annotation(
    x=3.5, y=9,
    text="Processing",
    showarrow=False,
    font=dict(size=12, color="black", family="Arial Black"),
    xanchor="center"
)

fig.add_annotation(
    x=6, y=9,
    text="Integration",
    showarrow=False,
    font=dict(size=12, color="black", family="Arial Black"),
    xanchor="center"
)

fig.add_annotation(
    x=8.5, y=9,
    text="Lattice Platform",
    showarrow=False,
    font=dict(size=12, color="black", family="Arial Black"),
    xanchor="center"
)

# Update layout
fig.update_layout(
    title="METAR to Lattice Integration System",
    xaxis=dict(
        range=[0, 10],
        showgrid=False,
        showticklabels=False,
        zeroline=False
    ),
    yaxis=dict(
        range=[3.5, 9.5],
        showgrid=False,
        showticklabels=False,
        zeroline=False
    ),
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

# Save the chart
fig.write_image("metar_lattice_architecture.png")