"""Conserva la demostración de lematización del Colab original."""
def main():
    import spacy
    nlp = spacy.load("es_core_news_sm")
    for verbo in ["trae", "lleva", "busca", "entrega"]:
        tokens = [t for t in nlp(verbo) if t.pos_ in {"VERB", "AUX"}]
        lema = tokens[0].lemma_.lower() if tokens else verbo.lower()
        print(verbo, "->", lema)

if __name__ == "__main__":
    main()
