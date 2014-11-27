#! /usr/bin/python
# -*- coding: utf-8 -*-


""" Generate pcap files from zep messages """

#
#  http://www.codeproject.com/Tips/612847/ \
#      Generate-a-quick-and-easy-custom-pcap-file-using-P

import sys
import binascii

PCAP_GLOBAL_HEADER = (
    'D4 C3 B2 A1'
    '02 00'         # File format major revision (i.e. pcap <2>.4)
    '04 00'         # File format minor revision (i.e. pcap 2.<4>)
    '00 00 00 00'
    '00 00 00 00'
    'FF FF 00 00'
    '01 00 00 00'
)

# pcap packet header that must preface every packet
PCAP_PACKET_HEADER = (
    'AA 77 9F 47'  # timestamp seconds  # TODO
    '90 A2 04 00'  # timestamps microseconds TODO
    'XX XX XX XX'  # Frame size (little endian) // number of octets in file
    'YY YY YY YY'  # Frame size (little endian) // real size not truncated
)

ETH_HEADER = (
    '00 00 00 00 00 00'  # Source Mac
    '00 00 00 00 00 00'  # Dest Mac
    '08 00'              # Protocol (0x0800 = IP)
)

IP_HEADER = (
    '45'           # IP version and healer length (multiples of 4 bytes)
    '00'
    'XX XX'        # Length - Will be calculated and replaced later
    '00 00'
    '40 00 40'
    '11'           # Protocol (0x11 = UDP)
    'YY YY'        # Checksum - Will be calculated and replaced later
    '7F 00 00 01'  # Source IP (Default: 127.0.0.1)
    '7F 00 00 01'  # Dest IP   (Default: 127.0.0.1)
)

UDP_HEADER = (
    '80 01'
    '45 5a'  # Port: ZepPort 17754 in hexa
    'YY YY'  # Length - Will be calculated and replaced later
    '00 00'
)


def get_byte_len(byte_str):
    """ Return the binascii string length """
    return len(''.join(byte_str.split())) / 2


def to_pcap(zep_message):
    """ generate pcap from binary message """

    udp_len = len(zep_message) + get_byte_len(UDP_HEADER)
    udp_h = UDP_HEADER.replace('YY YY', '%04x' % udp_len)

    ip_len = udp_len + get_byte_len(IP_HEADER)
    ip_h = IP_HEADER.replace('XX XX', '%04x' % ip_len)
    checksum = ip_checksum(ip_h.replace('YY YY', '00 00'))
    ip_h = ip_h.replace('YY YY', "%04x" % checksum)

    pcap_len = ip_len + get_byte_len(ETH_HEADER)
    hex_str = "%08x" % pcap_len
    # TODO check this with endiannes
    reverse_hex_str = hex_str[6:] + hex_str[4:6] + hex_str[2:4] + hex_str[:2]
    pcap_h = PCAP_PACKET_HEADER.replace('XX XX XX XX', reverse_hex_str)
    pcap_h = pcap_h.replace('YY YY YY YY', reverse_hex_str)

    bytestring = to_bin(pcap_h + ETH_HEADER + ip_h + udp_h) + zep_message
    return bytestring


def split_n(str1, num):
    """ Splits the string into a list of tokens every num characters """
    return [str1[start:start+num] for start in range(0, len(str1), num)]


def ip_checksum(iph):
    """ Calculates and returns the IP checksum based on the given IP Header """
    # split into bytes
    words = split_n(''.join(iph.split()), 4)
    csum = 0
    for word in words:
        csum += int(word, base=16)
    csum += (csum >> 16)
    csum = csum & 0xFFFF ^ 0xFFFF

    return csum


def to_bin(byte_string):
    """ Remove all whitespaces from binascii and return binary """
    return binascii.a2b_hex(''.join(byte_string.split()))


def main():
    """ Main function """

    zep_message_str = (
        '45 58 02 01'   # Base Zep header
        '0B 00 01 00 ff'   # chan | dev_id | dev_id| LQI/CRC_MODE |  LQI
        '00 00 00 00'   # Timestamp msb
        '00 00 00 00'   # timestamp lsp

        '00 00 00 01'   # seqno

        '00 01 02 03'   # reserved 0-3/10
        '04 05 16 07'   # reserved 4-7/10
        '08 09'         # reserved 8-9 / 10
        '08'            # Length 2 + data_len
        '61 62 63'      # Data
        '41 42 43'      # Data
        'FF FF'         # CRC)
    )
    zep_message = to_bin(zep_message_str)

    pcap_hdr = to_bin(PCAP_GLOBAL_HEADER)
    pcap_msg = to_pcap(zep_message)

    try:
        out_file = sys.argv[1]
        with open(out_file, 'w') as pcap_file:
            pcap_file.write(pcap_hdr)
            pcap_file.write(pcap_msg)
    except IndexError:
        out = binascii.b2a_hex(pcap_hdr)
        out += binascii.b2a_hex(pcap_msg)
        print out


if __name__ == '__main__':
    main()