from dependency_injector import containers, providers
from openai import AsyncOpenAI

from services import app
from services.app.agents import p0 as agents


class AssistantContainer(containers.DeclarativeContainer):
    search_service = providers.Dependency(app.AppSearchService)
    openai_client = providers.Dependency(AsyncOpenAI)

    model = providers.Dependency()
    temperature = providers.Dependency()

    p0 = providers.Factory(
        agents.P0,
        client=openai_client,
        temperature=temperature,
        model=model,
    )
    p0_1 = providers.Factory(
        agents.P0_1,
        client=openai_client,
        temperature=0.9,
        model="gpt-4o",
    )
    p0_2 = providers.Factory(
        agents.P0_2,
        client=openai_client,
        temperature=temperature,
        model=model,
    )
    p0_3 = providers.Factory(
        agents.P0_3,
        client=openai_client,
        temperature=temperature,
        model=model,
    )
    p0_4 = providers.Factory(
        agents.P0_4,
        client=openai_client,
        temperature=temperature,
        model=model,
    )

    assistant_service = providers.Factory(
        app.P0AssistantServiceV1,
        p0=p0,
        p0_1=p0_1,
        p0_2=p0_2,
        p0_3=p0_3,
        p0_4=p0_4,
        search_service=search_service,
    )
