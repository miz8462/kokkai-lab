from sudachipy import Dictionary, SplitMode

tokenizer_obj = Dictionary().tokenizer()
text = "国会で消費税の議論が行われた"
for m in tokenizer_obj.tokenize(text, SplitMode.C):
    print(m.surface(), m.part_of_speech()[0], m.dictionary_form())
