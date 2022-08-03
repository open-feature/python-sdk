from open_feature.evaluation_context.evaluation_context import EvaluationContext


def test_empty_evaluation_context_can_be_merged_with_non_empty_context():
    # Given
    empty_context = EvaluationContext()
    non_empty_context = EvaluationContext(
        targeting_key="targeting_key", attributes={"att1": "value1"}
    )

    # When
    merged_context = empty_context.merge(non_empty_context)

    # Then
    assert merged_context.attributes == non_empty_context.attributes
    assert merged_context.targeting_key == non_empty_context.targeting_key


def test_non_empty_context_can_be_merged_with_empty_evaluation_context():
    # Given
    empty_context = EvaluationContext()
    non_empty_context = EvaluationContext(
        targeting_key="targeting_key", attributes={"att1": "value1"}
    )

    # When
    merged_context = non_empty_context.merge(empty_context)

    # Then
    assert merged_context.attributes == non_empty_context.attributes
    assert merged_context.targeting_key == non_empty_context.targeting_key


def test_second_targeting_key_overwrites_first():
    # Given
    first_context = EvaluationContext(
        targeting_key="targeting_key1", attributes={"att1": "value1"}
    )
    second_context = EvaluationContext(
        targeting_key="targeting_key2", attributes={"att1": "value1"}
    )

    # When
    merged_context = first_context.merge(second_context)

    # Then
    assert merged_context.targeting_key == second_context.targeting_key
