"""Full text search index."""

import json
import string


class TextIndex:
    """Full text search index."""

    def __init__(self, datafile=None):
        """Init index."""
        if datafile is None:
            self.datafile = 'text_index.json'
        else:
            self.datafile = datafile

        self.data = None
        self.load()

    def _load(self):
        with open(self.datafile, 'r') as f:
            self.data = json.load(f)

    def load(self):
        """Load index from file."""
        try:
            self._load()
        except FileNotFoundError:
            self.data = {'items': []}
            self._dump()

    def _dump(self):
        with open(self.datafile, 'w') as f:
            json.dump(self.data, f)

    dump = _dump

    def _clear_text(self, text):
        cleared_text = ''.join((c for c in text
                                if c not in string.punctuation))
        return cleared_text

    def _vectorize(self, text):
        """Convert text string to vector for indexing or querying."""
        cleared_text = self._clear_text(text)
        vector = cleared_text.split(' ')
        return vector

    def index_document(self, summary, title, link):
        """Add document to index."""
        text = title + '. ' + summary
        vector = self._vectorize(text)
        item = {'vector': vector,
                'summary': summary,
                'title': title,
                'link': link}
        self.data['items'].append(item)

    def query(self, query_text, match_count=3):
        """Query index."""
        vector = self._vectorize(query_text)
        matches = []
        for item in self.data['items']:
            m = 0
            for i in vector:
                m += item['vector'].count(i)
            matches.append({'item': item,
                            'match': m})
        matches.sort(key=lambda j: j['match'], reverse=True)
        return {'items': [m['item'] for m in matches if m['match'] > 0]}


if __name__ == '__main__':
    i = TextIndex()

    summary1 = """The Ottoman wars in Europe, also known as the Ottoman Wars or Turkish Wars, were a series of military conflicts between the Ottoman Empire and various European states dating from the Late Middle Ages up through the early 20th century. The earliest conflicts began during the Byzantine–Ottoman Wars in the 13th century, followed by the Bulgarian–Ottoman Wars and the Serbian–Ottoman Wars in the 14th century. Much of this period was characterized by Ottoman expansion into the Balkans. The Ottoman Empire made further inroads into Central Europe in the 15th and 16th centuries, culminating in the peak of Turkish territorial claims in Europe."""
    title1 = "Ottoman wars in Europe"
    link1 = 'https://en.wikipedia.org/wiki/Ottoman_wars_in_Europe'
    i.index_document(summary1, title1, link1)

    summary2 = """Robyn Love was born in Ayr, Scotland, on 28 August 1990.[1] She was born with arthrogryposis, a rare condition in which the muscles are shortened, due to the umbilical cord being wrapped around her legs.[2] As a result, her right leg is shorter than her left, and she is missing muscles in both legs. At school she played football and tennis, but refused to participate in athletics because she knew her disability prevented her from running as fast as the other kids.[3] During her 2008 gap year before university, surgeons at Glasgow Royal Infirmary attempted to lengthen her leg by breaking it and using plaster and pins to keep it straight. The pins had to be tightened daily, which was excruciatingly painful. They also inserted a plate in her femur that helped her walk better, but her right leg remained 10 centimetres (3.9 in) shorter, and she still walked with a limp. In 2009, she entered Edinburgh Napier University, where she studied biomedical sciences. One of the first things she did was find sports organisations, and she started playing basketball.[2]"""
    title2 = "Robyn Love"
    link2 = 'https://en.wikipedia.org/wiki/Robyn_Love'
    i.index_document(summary2, title2, link2)

    summary3 = """The successor of Sony Alpha 77 model, the Sony Alpha 77 II is similar in design to its antecedent, including the use of a SLT transparent mirror and electronic viewfinder. It features a BIONZ X image processor and is compatible with A-mount lenses. GPS has been dropped in favour of Wi-Fi and NFC. The focus area is wider and denser, with a class-leading 79 AF points including 15 crossing sensor combined with subject tracking and eye-focus capabilities. The SLT design avoids the need to flip the mirror out of the way with every shot, allowing a rapid 12 fps burst speed for up to 60 frames in full resolution. Unlike most DSLR cameras, the phase-detect focus unit is operational during live-view and video (which is Full HD at 60p/50p and 24p/25p). The resolution of the camera is 24 megapixels. Sony's A-mount cameras feature in-body image stabilisation and the α77 II is the first of such to also stabilise the viewfinder when taking still images. ISO ranges from 50 to 25600. APS-C sized CMOS sensor."""
    title3 = "Sony Alpha 77 II"
    link3 = 'https://en.wikipedia.org/wiki/Sony_Alpha_77_II'
    i.index_document(summary3, title3, link3)

    i.dump()
