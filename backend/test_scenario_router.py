"""ScenarioRouter 单元测试."""

import pytest
from pathlib import Path
from scenario_router import ScenarioRouter, SCENARIO_PROMPTS


@pytest.fixture
def router():
    return ScenarioRouter()


class TestScenarioLoading:
    def test_loads_all_four_scenarios(self, router):
        scenarios = router.list_scenarios()
        assert len(scenarios) == 4
        ids = {s["id"] for s in scenarios}
        assert ids == {
            "popular_science",
            "classroom_teaching",
            "research_presentation",
            "long_term_learning",
        }

    def test_each_scenario_has_name_and_style(self, router):
        for s in router.list_scenarios():
            assert "id" in s
            assert "name" in s
            assert "style" in s
            assert len(s["name"]) > 0


class TestGetScenarioConfig:
    def test_valid_scenario_returns_config(self, router):
        config = router.get_scenario_config("popular_science")
        assert config["id"] == "popular_science"
        assert config["name"] == "科普传播"
        assert "output_types" in config

    def test_invalid_scenario_raises(self, router):
        with pytest.raises(ValueError, match="未知场景"):
            router.get_scenario_config("nonexistent")

    def test_all_four_scenarios_have_prompts(self, router):
        for s in router.list_scenarios():
            config = router.get_scenario_config(s["id"])
            assert isinstance(config, dict)
            assert config["id"] in SCENARIO_PROMPTS


class TestBuildSystemPrompt:
    def test_prompt_contains_scenario_name(self, router):
        prompt = router.build_system_prompt("popular_science", "test_user")
        assert "科普传播" in prompt
        assert "知己" in prompt
        assert "免疫系统如何识别病毒" in prompt

    def test_classroom_prompt_differs_from_popular_science(self, router):
        ps = router.build_system_prompt("popular_science", "u1")
        ct = router.build_system_prompt("classroom_teaching", "u1")
        assert ps != ct

    def test_research_prompt_contains_academic_tone(self, router):
        prompt = router.build_system_prompt("research_presentation", "u1")
        assert "科研展示" in prompt or "科研" in prompt

    def test_long_term_learning_prompt_contains_companion_tone(self, router):
        prompt = router.build_system_prompt("long_term_learning", "u1")
        assert "长期学习陪伴" in prompt or "学习陪伴" in prompt


class TestListScenarios:
    def test_returns_public_fields_only(self, router):
        scenarios = router.list_scenarios()
        for s in scenarios:
            assert set(s.keys()) == {"id", "name", "style"}
