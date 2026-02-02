from openfeature.track import TrackingEventDetails
import pytest

@pytest.mark.asyncio
async def test_add_attribute_to_tracking_event_details():
    tracking_event_details = TrackingEventDetails()
    tracking_event_details.add("key", "value")
    assert tracking_event_details.attributes == {"key": "value"}

@pytest.mark.asyncio
async def test_get_value_from_tracking_event_details():
    tracking_event_details = TrackingEventDetails(value=1)
    assert tracking_event_details.value == 1

@pytest.mark.asyncio
async def test_get_attributes_from_tracking_event_details():
    tracking_event_details = TrackingEventDetails(value=5.0, attributes={"key": "value"})
    assert tracking_event_details.attributes == {"key": "value"}

@pytest.mark.asyncio
async def test_get_attributes_from_tracking_event_details_with_none_value():
    tracking_event_details = TrackingEventDetails(attributes={"key": "value"})
    assert tracking_event_details.attributes == {"key": "value"}
    assert tracking_event_details.value is None

@pytest.mark.asyncio
async def test_get_attributes_from_tracking_event_details_with_none_attributes():
    tracking_event_details = TrackingEventDetails(value=5.0)
    assert tracking_event_details.attributes == {}
    assert tracking_event_details.value == 5.0
