#include <uapi/linux/if_ether.h>
#include <uapi/linux/in6.h>
#include <uapi/linux/ipv6.h>
#include <uapi/linux/pkt_cls.h>
#include <uapi/linux/bpf.h>
#include <bcc/proto.h>
//#include <uapi/linux/tcp.h>
#include <net/tcp.h>

#define IP_ICMP 1
#define IP_TCP  6

struct Key {
	u32 global_index;         //Global count of the packet
	u32 ifindex;              //The interface that captured the packet
};

struct SegmentData {
	u32 src_ip;               //source ip
	u32 dst_ip;               //destination ip
	unsigned short src_port;  //source port
	unsigned short dst_port;  //destination port
	int length;		   // packet length
	u64 timestamp;            //timestamp in ns
};

struct SegmentDataExt {
	u32 tsval;		   //TSVal field, if exists in options, or 0 if not.
	u32 seq_num; 
};

struct opt_char_t
{
    char c;
} BPF_PACKET_HEADER;

struct OptChars {
  unsigned char p[40];
};

BPF_HASH(pkt_array, struct Key, struct SegmentData,5000000);
BPF_HASH(pkt_array_ext, struct Key, struct SegmentDataExt,5000000);
BPF_ARRAY(pkt_out_count, uint32_t, 1);
BPF_ARRAY(pkt_count, uint32_t, 1);
BPF_ARRAY(debug_val, long, 1);
BPF_ARRAY(sniff_mode, uint32_t, 1);
BPF_ARRAY(start_time, u64, 1);

int out_filter(struct __sk_buff *skb)
{
    handle_egress(skb);
    return TC_ACT_OK;
}

int handle_egress(struct __sk_buff *skb)
{
    int one = 1;
    u32 intkey = 0;
    u32  tcp_header_length = 0;
    u32  ip_header_length = 0;
    u64 start_ts = 0;
    u64* start_ts_ptr = 0;
    long  options_offset = 0;
    long  options_length = 0;
    u32  tsval = 0;
    struct OptChars opt_chars = {};

    uint32_t* global_count = 0;
    uint32_t* mode = 0;
    long* pkt_index = 0;
    struct Key 	key;
    struct SegmentData segment_data;
    struct SegmentDataExt segment_data_ext;

    u8 *cursor = 0;

    // initialize the capture start time
    start_ts_ptr = start_time.lookup(&intkey);
    if (!start_ts_ptr) {
        start_time.update(&intkey, &start_ts);
        start_ts_ptr = start_time.lookup(&intkey);
    } else{
        if (*start_ts_ptr == 0) {
            start_ts += bpf_ktime_get_ns()/1000;
            start_time.update(&intkey, &start_ts);
        }
    }

    //start_ts = bpf_ktime_get_ns();

    // if sniff mode is not set to 1, do not capture anything
    mode = sniff_mode.lookup(&intkey);
    if (mode) { // check if this map exists
        if(*mode!=1){
            goto ACT_OK;
        } else {
            //if (*start_ts_ptr == 0) {
                //
            //}
        }
    }

    
    long yyy = 123;
    debug_val.update(&intkey, &yyy); 
    struct ethernet_t *ethernet = cursor_advance(cursor, sizeof(*ethernet));
    //if not IP packet, then pass the packet and return
    if (!(ethernet->type == 0x0800)) {
        long ooo = 211;
        debug_val.update(&intkey, &ooo); 
        goto ACT_OK;
    }

    struct ip_t *ip = cursor_advance(cursor, sizeof(*ip));
    //if not TCP packet, then pass the packet and return
    if (ip->nextp != IP_TCP) {
        long iii = 322;
        debug_val.update(&intkey, &iii); 
        goto ACT_OK;
    }
        
    // From this point on, we assume that we want to add the packet to the array.
    // The core returned for all the packets that should be filtered out.

    // count number of packets
    global_count = pkt_count.lookup(&intkey);
    if (global_count) { // check if this map exists
        *global_count+=1;
    }
    else        // if the map for the key doesn't exist, create one
    {
        pkt_count.update(&intkey, &one);
    }

    struct tcp_t *tcp = cursor_advance(cursor, sizeof(*tcp));

    // Extract TCP source port. If not 64501 (which corresponds with online)simulation.py)
    // then filter out.
    // TODO: make this condition more configurable. Maybe as parameter?
    uint16_t src_port = tcp->src_port;
    if (src_port < 64501 || src_port > 64599){
        goto ACT_OK;
    }

    // Extract TSVal out of TCP options
    //calculate tcp header length
    //value to multiply *4
    //e.g. tcp->offset = 5 ; TCP Header Length = 5 x 4 byte = 20 byte
    ip_header_length = ip->hlen << 2;    //SHL 2 -> *4 multiply    
    tcp_header_length = tcp->offset << 2; //SHL 2 -> *4 multiply


    //calculate payload offset and length
    options_offset = ETH_HLEN + ip_header_length + 20; //20 is the size of TCP header without options
    options_length = tcp_header_length-20; 
    if ((options_length<10)) { //TSVal alone is 10 bytes
        long ppp = 766;
        debug_val.update(&intkey, &ppp); 
        goto ACT_OK;
    }

    tsval = 111;
    if(options_length>=10) {
        ///long lll = 699;
        ///debug_val.update(&intkey, &options_offset);    
        long ddd = 777;
        debug_val.update(&intkey, &ddd);
        u16 loc = 0;
        u16 i = 0;
        struct opt_char_t *c;
        #pragma unroll
        for(i = 0; i<12;i++){
          c = cursor_advance(cursor, 1);
          opt_chars.p[i] = c->c;
          if (c->c == TCPOPT_TIMESTAMP)
            loc = i;
        }
        if (loc <5) {
           tsval = opt_chars.p[loc+2] << 24| (opt_chars.p[loc+3] << 16) | (opt_chars.p[loc+4] << 8) | (opt_chars.p[loc+5] );
        }

        int cnt = 0;
        
    }

        
    // Build the key
    if (global_count) {
        key.global_index = *global_count;
    } else {
        key.global_index = 1;
    }

    key.ifindex = skb->ifindex;

    //retrieve ip src/dest and port src/dest of current packet
    //and save it into struct Key
    segment_data.src_ip = ip->src;
    segment_data.dst_ip = ip->dst;
    segment_data.src_port = tcp->src_port;
    segment_data.dst_port = tcp->dst_port;
    segment_data.length = skb->len;
    segment_data.timestamp = bpf_ktime_get_ns()/1000;
    segment_data_ext.tsval = tsval;
    segment_data_ext.seq_num = tcp->seq_num;
    
    
    pkt_array.insert(&key, &segment_data);
    pkt_array_ext.insert(&key, &segment_data_ext);

        
    ACT_OK:
    return TC_ACT_OK;
    

}
