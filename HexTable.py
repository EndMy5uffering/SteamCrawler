
def convert_to_hex(message):
    return [hex(ord(c))[2:] for c in message]

def print_hex_table(data):
    if len(data)%16 != 0:
        for _ in range((16-len(data)%16)):
            data.append('00')

    to = len(data) + (16-len(data)%16) if not len(data)%16==0 else len(data)

    for i in range(0, to, 16):
        line = hex(i)[2:]
        line = '0'*(4-len(line)) + line
        print(line + ':', ' '.join(data[i:i+16]))
        pass

if __name__=='__main__':
    message = 'Congratulations you just wasted your time translating this message :)'
    o = convert_to_hex(message)
    print_hex_table(o)

    print([hex(ord(c)) for c in message])
