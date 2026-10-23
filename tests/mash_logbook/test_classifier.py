from automation.mash_logbook import classifier


def test_commit_type_reads_conventional_prefix():
    assert classifier.commit_type("feat(auth): login") == "Funcionalidade"
    assert classifier.commit_type("fix!: corrigir 404") == "Correção"
    assert classifier.commit_type("Docs: README") == "Documentação"
    assert classifier.commit_type("ajustes gerais") == "Outro"


def test_issue_refs_default_to_mash_and_ignore_merged_pr_number():
    assert classifier.issue_refs("docs: alinhar decisões (#66)") == ["conloq/mash#66"]
    assert classifier.issue_refs("fix: tela Closes conloq/frontend#4 e #6") == ["conloq/frontend#4", "conloq/mash#6"]
    assert classifier.issue_refs("Merge pull request #11 from conloq/docs/66-x") == []


def test_sanitize_removes_tokens_and_emails():
    texto = classifier.sanitize("chave ghp_" + "a" * 30 + " de joao@exemplo.com")
    assert "ghp_" not in texto and "@exemplo" not in texto
    assert texto.count("[removido]") == 2


def test_merge_commits_are_detected():
    assert classifier.is_merge("Merge pull request #3 from x", 1)
    assert classifier.is_merge("qualquer", 2)
    assert not classifier.is_merge("feat: x", 1)
