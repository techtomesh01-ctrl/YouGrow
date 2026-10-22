from urllib.parse import urlparse

# Only permitted in-app tasks can earn points. Do not add YouTube engagement here.
POINT_RULES = {"profile_completed": 10, "tutorial_completed": 5}
FORBIDDEN_REWARD_ACTIONS = {
    "youtube_subscribe", "youtube_view", "youtube_like",
    "youtube_comment", "youtube_share", "sub4sub"
}

def validate_youtube_url(value):
    try:
        p = urlparse((value or "").strip())
        return p.scheme == "https" and p.hostname in {
            "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"
        }
    except Exception:
        return False
