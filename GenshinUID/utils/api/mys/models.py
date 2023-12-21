from typing import List, Literal, TypedDict


class Expedition(TypedDict):
    avatar_side_icon: str
    status: Literal['Ongoing', 'Finished']


class RecoveryTime(TypedDict):
    Day: int
    Hour: int
    Minute: int
    Second: int
    reached: bool


class Transformer(TypedDict):
    obtained: bool
    recovery_time: RecoveryTime
    wiki: str
    noticed: bool
    latest_job_id: str


class TaskStatus(TypedDict):
    status: str


class DayilyTask(TypedDict):
    total_num: int
    finished_num: int
    is_extra_task_reward_received: bool
    task_rewards: List[TaskStatus]
    attendance_rewards: List[TaskStatus]


class ArchonStatus(TypedDict):
    status: str
    chapter_num: str
    chapter_title: str
    id: int


class ArchonProgress(TypedDict):
    list: List[ArchonStatus]
    is_open_archon_quest: bool
    is_finish_all_mainline: bool
    is_finish_all_interchapter: bool
    wiki_url: str


class WidgetResin(TypedDict):
    current_resin: int
    max_resin: int
    resin_recovery_time: str
    finished_task_num: int
    total_task_num: int
    is_extra_task_reward_received: bool
    current_expedition_num: int
    max_expedition_num: int
    expeditions: List[Expedition]
    current_home_coin: int
    max_home_coin: int
    has_signed: bool
    sign_url: str
    home_url: str
    note_url: str


class FakeResin(WidgetResin):
    remain_resin_discount_num: int
    resin_discount_num_limit: int
    transformer: Transformer
    daily_task: DayilyTask
    archon_quest_progress: ArchonProgress
