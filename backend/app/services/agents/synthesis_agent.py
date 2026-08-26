"""Synthesis Agent — combines outputs from multiple agents into a unified answer."""

from __future__ import annotations

from app.services.agents.base import AgentResult, Source


class SynthesisAgent:
    """Merges multiple agent results into a single coherent response."""

    name = "synthesis"

    async def synthesize(
        self,
        query: str,
        results: list[AgentResult],
        ai_gateway=None,
        byok_key: str | None = None,
    ) -> AgentResult:
        """Combine multiple agent results into one unified answer.

        If an AI gateway is available, uses an LLM to produce a coherent synthesis.
        Otherwise, concatenates the results with headers.
        """
        if not results:
            return AgentResult(agent_name=self.name, answer="No agent results to synthesize.", confidence=0.0)

        if len(results) == 1:
            return results[0]

        # Merge all sources (deduplicated)
        all_sources: list[Source] = []
        seen = set()
        for r in results:
            for s in r.sources:
                key = (s.file_path, s.start_line, s.end_line)
                if key not in seen:
                    seen.add(key)
                    all_sources.append(s)

        # Build combined context from all agent outputs
        agent_sections = []
        for r in results:
            agent_sections.append(f"=== {r.agent_name} (confidence: {r.confidence:.1f}) ===\n{r.answer}")

        combined = "\n\n".join(agent_sections)

        # Try LLM synthesis for a coherent merged answer
        if ai_gateway:
            system = (
                "You are AskRepo's Synthesis Agent. Multiple specialized analysts have provided "
                "their findings about a repository. Combine their outputs into a single, coherent, "
                "well-structured answer.\n"
                "Rules:\n"
                "1. Integrate insights from all analysts — don't just list them sequentially.\n"
                "2. Remove redundancy — if two analysts mention the same thing, include it once.\n"
                "3. Preserve all source citations (file:line format).\n"
                "4. Structure the answer with clear markdown headings.\n"
                "5. Prioritize the most relevant information for the user's question."
            )
            user_prompt = (
                f"User question: {query}\n\n"
                f"Analyst findings:\n\n{combined}\n\n"
                f"Provide a single unified answer."
            )
            try:
                answer, _ = await ai_gateway.generate(
                    prompt=user_prompt, system=system, byok_key=byok_key,
                )
                # Average confidence
                avg_conf = sum(r.confidence for r in results) / len(results)
                return AgentResult(
                    agent_name=self.name,
                    answer=answer,
                    sources=all_sources,
                    confidence=avg_conf,
                    used_llm=True,
                )
            except Exception:
                pass

        # Fallback: concatenate with headers
        fallback_parts = []
        for r in results:
            fallback_parts.append(f"### {r.agent_name.replace('_', ' ').title()}\n\n{r.answer}")
        fallback_answer = "\n\n---\n\n".join(fallback_parts)

        return AgentResult(
            agent_name=self.name,
            answer=fallback_answer,
            sources=all_sources,
            confidence=sum(r.confidence for r in results) / len(results),
            used_llm=False,
        )
