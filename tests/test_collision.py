"""Tests for collision detection."""
import sys
sys.path.insert(0, '.')
from core.collision import segment_intersects_circle, blade_hits_entity


def test_segment_hits_circle():
    # Line through center
    assert segment_intersects_circle((0, 0), (10, 0), 5, 0, 3) == True
    # Line misses
    assert segment_intersects_circle((0, 10), (10, 10), 5, 0, 3) == False
    # Line just touches
    assert segment_intersects_circle((0, 3), (10, 3), 5, 0, 3) == True
    # Segment too short
    assert segment_intersects_circle((0, 0), (1, 0), 5, 0, 1) == False
    # Point inside circle
    assert segment_intersects_circle((5, 0), (5, 0), 5, 0, 3) == True
    print("[OK] All collision tests passed!")


def test_blade_hits():
    segments = [((0, 0), (5, 5)), ((5, 5), (10, 10))]
    assert blade_hits_entity(segments, 5, 5, 3) == True
    assert blade_hits_entity(segments, 50, 50, 3) == False
    print("[OK] All blade tests passed!")


if __name__ == "__main__":
    test_segment_hits_circle()
    test_blade_hits()
