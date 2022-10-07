from typing import List


async def get_all_friend_list(bot) -> List[int]:
    friend_list = []
    friend_dict_list = await bot.call_action(action='get_friend_list')
    for friend in friend_dict_list:
        friend_list.append(friend['user_id'])
    return friend_list


async def get_group_member_list(bot, group_id: int) -> List[int]:
    member_list = []
    group_member_list = await bot.call_api(
        action='get_group_member_list', group_id=group_id
    )
    for group_member in group_member_list:
        member_list.append(group_member['user_id'])
    return member_list
