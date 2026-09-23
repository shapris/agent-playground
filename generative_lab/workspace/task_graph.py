"""Small dependency graph used by the PUPIS generative-coder proof."""

class TaskGraph:
    def __init__(self, dependencies):
        if not isinstance(dependencies, dict):
            raise TypeError("dependencies must be a mapping")
        self._deps = {str(task): {str(dep) for dep in deps} for task, deps in dependencies.items()}
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
        done = {str(item) for item in completed}
        ready = [
            task
            for task, deps in self._deps.items()
            if task not in done and deps.issubset(done)
        ]
        return sorted(ready)
