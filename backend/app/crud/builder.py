from typing import Optional

from beanie import PydanticObjectId

from app.models.builder_option import BuilderOption, BuilderOptionType


async def create_option(data: dict) -> BuilderOption:
    opt = BuilderOption(**data)
    await opt.insert()
    return opt


async def list_options(
    option_type: Optional[BuilderOptionType] = None,
    available_only: bool = False,
) -> list[BuilderOption]:
    query = BuilderOption.find()
    if option_type:
        query = query.find(BuilderOption.type == option_type)
    if available_only:
        query = query.find(BuilderOption.is_available == True)  # noqa: E712
    return await query.sort(+BuilderOption.display_order).to_list()


async def get_grouped() -> dict[str, list[BuilderOption]]:
    all_opts = await BuilderOption.find(
        BuilderOption.is_available == True  # noqa: E712
    ).sort(+BuilderOption.display_order).to_list()

    grouped: dict[str, list[BuilderOption]] = {
        "bases": [],
        "proteins": [],
        "sauces": [],
        "toppings": [],
    }
    type_map = {
        BuilderOptionType.BASE: "bases",
        BuilderOptionType.PROTEIN: "proteins",
        BuilderOptionType.SAUCE: "sauces",
        BuilderOptionType.TOPPING: "toppings",
    }
    for opt in all_opts:
        grouped[type_map[opt.type]].append(opt)
    return grouped


async def get_option(opt_id: str) -> Optional[BuilderOption]:
    try:
        return await BuilderOption.get(PydanticObjectId(opt_id))
    except Exception:
        return None


async def update_option(opt: BuilderOption, data: dict) -> BuilderOption:
    for k, v in data.items():
        if v is not None:
            setattr(opt, k, v)
    await opt.save()
    return opt


async def delete_option(opt: BuilderOption) -> None:
    await opt.delete()