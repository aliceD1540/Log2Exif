import json
import datetime
import bisect

def parse_geo_point(point_str):
    """
    Parses string "35.6978689°, 139.7731628°" into (lat, lon) floats.
    """
    try:
        parts = point_str.split(',')
        lat = float(parts[0].strip().replace('°', ''))
        lon = float(parts[1].strip().replace('°', ''))
        return lat, lon
    except (ValueError, IndexError):
        return None, None

def parse_timestamp(time_str):
    """
    Parses ISO 8601 string to datetime object.
    """
    try:
        return datetime.datetime.fromisoformat(time_str)
    except ValueError:
        return None

def load_timeline_points(json_path):
    """
    Loads the timeline JSON and returns a sorted list of (timestamp, lat, lon).
    Extracts points from 'timelinePath' inside 'semanticSegments'.
    """
    points = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        segments = data.get('semanticSegments', [])
        for segment in segments:
            timeline = segment.get('timelinePath', [])
            if not timeline:
                # Fallback: check if 'visit' or 'activity' has start/end location and time
                # Ideally we prefer high density points, but start/end is better than nothing if needed.
                # For now, let's stick to timelinePath or strict design requirements.
                # Design says: "Google Maps Timeline JSON".
                pass

            for point in timeline:
                p_str = point.get('point')
                t_str = point.get('time')
                if p_str and t_str:
                    lat, lon = parse_geo_point(p_str)
                    dt = parse_timestamp(t_str)
                    if lat is not None and lon is not None and dt is not None:
                        points.append((dt, lat, lon))
                        
    except Exception as e:
        print(f"Error loading timeline: {e}")
        return []

    # Sort by timestamp just in case
    points.sort(key=lambda x: x[0])
    return points

def find_nearest_point(target_time, points):
    """
    Finds the (lat, lon) from 'points' closest in time to target_time.
    Points is a list of (datetime, lat, lon), sorted by datetime.
    """
    if not points:
        return None

    # Use bisect to find insertion point
    timestamps = [p[0] for p in points]
    idx = bisect.bisect_left(timestamps, target_time)

    # Check idx and idx-1 to see which is closer
    candidates = []
    if idx < len(points):
        candidates.append(points[idx])
    if idx > 0:
        candidates.append(points[idx - 1])

    if not candidates:
        return None

    best_point = min(candidates, key=lambda p: abs(p[0] - target_time))
    
    # Optional: Define a threshold? Design doesn't specify one, just "closest time".
    return best_point[1], best_point[2]
