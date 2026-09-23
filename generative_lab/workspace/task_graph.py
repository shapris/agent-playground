"""Small dependency graph used by the PUPIS generative-coder proof."""

from collections.abc import Collection


class TaskGraph:
    def __init__(self, dependencies):
        if not isinstance(dependencies, dict):
            raise TypeError("dependencies must be a mapping")

        self._deps = {}
        for task, deps in dependencies.items():
            if not isinstance(task, str) or not task:
                raise ValueError("task identifiers must be non-empty strings")
            if task in self._deps:
                raise ValueError(f"duplicate task identifier: {task}")
            if isinstance(deps, (str, bytes)) or not isinstance(deps, Collection):
                raise ValueError("dependencies for each task must be a non-string collection")

            normalized_deps = set()
            for dep in deps:
                if not isinstance(dep, str) or not dep:
                    raise ValueError("dependency identifiers must be non-empty strings")
                normalized_deps.add(dep)
            self._deps[task] = normalized_deps

        missing = set().union(*self._deps.values()) - set(self._deps) if self._deps else set()
        for task in missing:
            self._deps[task] = set()
        self._assert_acyclic()

    def _assert_acyclic(self):
        visiting = set()
        visited = set()

        def visit(task):
            if task in visiting:
                raise ValueError(f"dependency cycle detected at {task}")
            if task in visited:
                return
            visiting.add(task)
            for dep in self._deps[task]:
                visit(dep)
            visiting.remove(task)
            visited.add(task)

        for task in self._deps:
            visit(task)

    def ready_tasks(self, completed=()):
        if isinstance(completed, (str, bytes)) or not isinstance(completed, Collection):
            raise ValueError("completed tasks must be a non-string collection")

        done = set()
        for item in completed:
            if not isinstance(item, str) or not item:
                raise ValueError("completed task identifiers must be non-empty strings")
            done.add(item)

        ready = [
            task
            for task, deps in self._deps.items()
            if task not in done and deps.issubset(done)
        ]
        return sorted(ready)
