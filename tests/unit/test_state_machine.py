"""Tests for the experiment state machine."""

import pytest

from agentml.core.state_machine import (
    ExperimentState,
    InvalidTransitionError,
    transition,
)


def test_pending_to_running():
    result = transition(ExperimentState.PENDING, ExperimentState.RUNNING)
    assert result == ExperimentState.RUNNING


def test_running_to_completed():
    result = transition(ExperimentState.RUNNING, ExperimentState.COMPLETED)
    assert result == ExperimentState.COMPLETED


def test_running_to_failed():
    result = transition(ExperimentState.RUNNING, ExperimentState.FAILED)
    assert result == ExperimentState.FAILED


def test_completed_to_archived():
    result = transition(ExperimentState.COMPLETED, ExperimentState.ARCHIVED)
    assert result == ExperimentState.ARCHIVED


def test_failed_to_archived():
    result = transition(ExperimentState.FAILED, ExperimentState.ARCHIVED)
    assert result == ExperimentState.ARCHIVED


def test_invalid_pending_to_completed():
    with pytest.raises(InvalidTransitionError):
        transition(ExperimentState.PENDING, ExperimentState.COMPLETED)


def test_invalid_completed_to_running():
    with pytest.raises(InvalidTransitionError):
        transition(ExperimentState.COMPLETED, ExperimentState.RUNNING)


def test_invalid_archived_to_anything():
    with pytest.raises(InvalidTransitionError):
        transition(ExperimentState.ARCHIVED, ExperimentState.RUNNING)
