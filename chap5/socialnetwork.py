from PIL import Image, ImageDraw

people = ['Charlie', 'Augustus', 'Veruca', 'Violet', 'Mike', 'Joe', 'Willy',
        'Miranda']

links = [('Augustus', 'Willy'),
        ('Mike', 'Joe'),
        ('Miranda', 'Mike'),
        ('Violet', 'Augustus'),
        ('Miranda', 'Willy'),
        ('Charlie', 'Mike'),
        ('Veruca', 'Joe'),
        ('Miranda', 'Augustus'),
        ('Willy', 'Augustus'),
        ('Joe', 'Charlie'),
        ('Veruca', 'Augustus'),
        ('Miranda', 'Joe')]

domain = [(10, 370)] * (len(people) * 2)


def cross_count(v):
    loc = dict([(people[i], (v[i*2], v[i*2+1]))
        for i in xrange(0, len(people))])
    total = 0

    for i in xrange(len(links)):
        for j in xrange(i + 1, len(links)):
            (x1, y1), (x2, y2) = loc[links[i][0]], loc[links[i][1]]
            (x3, y3), (x4, y4) = loc[links[j][0]], loc[links[j][1]]

            den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            if den == 0:
                continue

            ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / float(den)
            ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / float(den)

            if ua > 0 and ua < 1 and ub > 0 and ub < 1:
                total += 1

    for i in xrange(len(people)):
        for j in xrange(i + 1, len(people)):
            (x1, y1), (x2, y2) = loc[people[i]], loc[people[j]]

            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if dist < 50:
                total += (1.0 - (dist / 50.0))

    return total


def draw_network(sol):
    img = Image.new('RGB', (400, 400), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    pos = dict([(people[i], (sol[i*2], sol[i*2+1]))
        for i in xrange(0, len(people))])

    for (a, b) in links:
        draw.line((pos[a], pos[b]), fill=(255, 0, 0))

    for n, p in pos.items():
        draw.text(p, n, (0, 0, 0))

    img.show()


