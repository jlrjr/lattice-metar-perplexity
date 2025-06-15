import pandas as pd
import plotly.graph_objects as go
import json

# Parse the data
data = {
  "airports": [
    {"icao": "KBOS", "name": "General Edward Lawrence Logan International Airport", "city": "Boston", "state": "MA", "type": "International", "major": True},
    {"icao": "KORH", "name": "Worcester Regional Airport", "city": "Worcester", "state": "MA", "type": "Regional", "major": False},
    {"icao": "KBED", "name": "Laurence G. Hanscom Field", "city": "Bedford", "state": "MA", "type": "Municipal", "major": False},
    {"icao": "KACK", "name": "Nantucket Memorial Airport", "city": "Nantucket", "state": "MA", "type": "Regional", "major": False},
    {"icao": "KMVT", "name": "Martha's Vineyard Airport", "city": "Martha's Vineyard", "state": "MA", "type": "Regional", "major": False},
    {"icao": "KHYA", "name": "Barnstable Municipal Airport", "city": "Hyannis", "state": "MA", "type": "Municipal", "major": False},
    {"icao": "KMHT", "name": "Manchester-Boston Regional Airport", "city": "Manchester", "state": "NH", "type": "Regional", "major": True},
    {"icao": "KLEB", "name": "Lebanon Municipal Airport", "city": "Lebanon", "state": "NH", "type": "Municipal", "major": False},
    {"icao": "KCON", "name": "Concord Municipal Airport", "city": "Concord", "state": "NH", "type": "Municipal", "major": False},
    {"icao": "KBDL", "name": "Bradley International Airport", "city": "Hartford/Windsor Locks", "state": "CT", "type": "International", "major": True},
    {"icao": "KHVN", "name": "Tweed New Haven Airport", "city": "New Haven", "state": "CT", "type": "Regional", "major": False},
    {"icao": "KGON", "name": "Groton-New London Airport", "city": "Groton/New London", "state": "CT", "type": "Municipal", "major": False},
    {"icao": "KPVD", "name": "Theodore Francis Green Airport", "city": "Providence/Warwick", "state": "RI", "type": "International", "major": True},
    {"icao": "KBTV", "name": "Patrick Leahy Burlington International Airport", "city": "Burlington", "state": "VT", "type": "International", "major": True},
    {"icao": "KMPV", "name": "Edward F. Knapp State Airport", "city": "Montpelier", "state": "VT", "type": "Municipal", "major": False},
    {"icao": "KBGR", "name": "Bangor International Airport", "city": "Bangor", "state": "ME", "type": "International", "major": True},
    {"icao": "KPWM", "name": "Portland International Jetport", "city": "Portland", "state": "ME", "type": "International", "major": False},
    {"icao": "KAUG", "name": "Augusta State Airport", "city": "Augusta", "state": "ME", "type": "Municipal", "major": False},
    {"icao": "KBHB", "name": "Hancock County-Bar Harbor Airport", "city": "Bar Harbor", "state": "ME", "type": "Municipal", "major": False}
  ]
}

# Convert to DataFrame
df = pd.DataFrame(data["airports"])

# Define colors for states (using brand colors)
state_colors = {
    'MA': '#1FB8CD',  # Strong cyan
    'NH': '#FFC185',  # Light orange  
    'CT': '#ECEBD5',  # Light green
    'RI': '#5D878F',  # Cyan
    'VT': '#D2BA4C',  # Moderate yellow
    'ME': '#B4413C'   # Moderate red
}

# Define symbols for airport types
type_symbols = {
    'International': 'diamond',
    'Regional': 'circle',
    'Municipal': 'square'
}

# Create abbreviated names for display (under 15 chars)
def abbreviate_name(name):
    if len(name) <= 15:
        return name
    # Common abbreviations
    abbrevs = {
        'International': 'Intl',
        'Regional': 'Rgnl',
        'Municipal': 'Muni',
        'Airport': 'Arpt',
        'General': 'Gen',
        'Edward': 'Ed',
        'Lawrence': 'L',
        'Memorial': 'Mem',
        'County': 'Co'
    }
    result = name
    for full, abbrev in abbrevs.items():
        result = result.replace(full, abbrev)
    if len(result) > 15:
        result = result[:12] + "..."
    return result

def abbreviate_city(city):
    if len(city) <= 12:
        return city
    return city[:9] + "..."

df['display_name'] = df['name'].apply(abbreviate_name)
df['display_city'] = df['city'].apply(abbreviate_city)

# Create grid positions for better spacing
state_order = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT']
x_positions = {state: i for i, state in enumerate(state_order)}

# Assign positions within each state column
df['x_pos'] = df['state'].map(x_positions)
df['y_pos'] = 0

# Create y positions with better spacing
for state in state_order:
    state_airports = df[df['state'] == state].sort_values(['major', 'type'], ascending=[False, True])
    for i, idx in enumerate(state_airports.index):
        df.loc[idx, 'y_pos'] = -i * 0.8  # Better vertical spacing

# Create the figure
fig = go.Figure()

# Add traces by state and major status for cleaner legend
for state in state_order:
    state_data = df[df['state'] == state]
    
    if len(state_data) == 0:
        continue
    
    # Major airports
    major_data = state_data[state_data['major'] == True]
    if len(major_data) > 0:
        fig.add_trace(go.Scatter(
            x=major_data['x_pos'],
            y=major_data['y_pos'],
            mode='markers+text',
            marker=dict(
                size=25,
                color=state_colors[state],
                symbol=[type_symbols[t] for t in major_data['type']],
                line=dict(width=3, color='black')
            ),
            text=major_data['icao'],
            textposition='top center',
            textfont=dict(size=10, color='black'),
            hovertext=[f"{row['icao']} - {row['display_name']}<br>({row['display_city']})<br>Type: {row['type']}<br>Status: Major" 
                      for _, row in major_data.iterrows()],
            hoverinfo='text',
            name=f"{state} Major",
            showlegend=True,
            cliponaxis=False
        ))
    
    # Regular airports
    regular_data = state_data[state_data['major'] == False]
    if len(regular_data) > 0:
        fig.add_trace(go.Scatter(
            x=regular_data['x_pos'],
            y=regular_data['y_pos'],
            mode='markers+text',
            marker=dict(
                size=15,
                color=state_colors[state],
                symbol=[type_symbols[t] for t in regular_data['type']],
                line=dict(width=1, color='gray')
            ),
            text=regular_data['icao'],
            textposition='top center',
            textfont=dict(size=8, color='black'),
            hovertext=[f"{row['icao']} - {row['display_name']}<br>({row['display_city']})<br>Type: {row['type']}" 
                      for _, row in regular_data.iterrows()],
            hoverinfo='text',
            name=f"{state} Regular",
            showlegend=True,
            cliponaxis=False
        ))

# Update layout
fig.update_layout(
    title="New England METAR Coverage",
    xaxis_title="States",
    yaxis_title="",
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(state_order))),
        ticktext=[f"{state}\n({len(df[df['state']==state])} airports)" for state in state_order],
        showgrid=False,
        range=[-0.5, len(state_order)-0.5]
    ),
    yaxis=dict(
        showticklabels=False, 
        showgrid=False,
        range=[df['y_pos'].min()-0.5, df['y_pos'].max()+1]
    ),
    hovermode='closest',
    showlegend=True,
    plot_bgcolor='white'
)

# Update axes
fig.update_xaxes(tickangle=0)
fig.update_yaxes(showticklabels=False)

# Save the chart
fig.write_image("new_england_airports.png")