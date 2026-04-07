// Package models contains data types for the SonicOS REST API.
package models

import "fmt"

// AddressObjectType represents the type of an IPv4 address object.
type AddressObjectType string

const (
	// AddressObjectTypeHost is a single host IP address.
	AddressObjectTypeHost AddressObjectType = "host"
	// AddressObjectTypeNetwork is a subnet (network/mask).
	AddressObjectTypeNetwork AddressObjectType = "network"
	// AddressObjectTypeRange is an IP address range.
	AddressObjectTypeRange AddressObjectType = "range"
	// AddressObjectTypeFQDN is a fully qualified domain name.
	AddressObjectTypeFQDN AddressObjectType = "fqdn"
	// AddressObjectTypeMAC is a MAC address.
	AddressObjectTypeMAC AddressObjectType = "mac"
)

// AddressObjectIPv4 is a SonicOS IPv4 address object.
//
// Only one of Host, Network, Range, FQDN, or MAC should be set,
// corresponding to the Type field.
type AddressObjectIPv4 struct {
	Name string            `json:"name"`
	Zone string            `json:"zone"`
	Type AddressObjectType `json:"-"` // Determined from which field is populated
	// Host address (type=host)
	Host string `json:"host,omitempty"`
	// Network (type=network)
	Network string `json:"network,omitempty"` // CIDR notation e.g. "10.0.0.0/24"
	// Range (type=range)
	RangeStart string `json:"range_start,omitempty"`
	RangeEnd   string `json:"range_end,omitempty"`
	// FQDN (type=fqdn)
	FQDN string `json:"fqdn,omitempty"`
	// MAC (type=mac)
	MAC string `json:"mac,omitempty"`
}

// Wire format types for marshalling/unmarshalling

type addressObjectHostWire struct {
	IP string `json:"ip"`
}

type addressObjectNetworkWire struct {
	Subnet string `json:"subnet"`
	Mask   string `json:"mask"`
}

type addressObjectRangeWire struct {
	Begin string `json:"begin"`
	End   string `json:"end"`
}

type addressObjectFQDNWire struct {
	Domain string `json:"domain"`
}

type addressObjectMACWire struct {
	Address string `json:"address"`
}

// AddressObjectIPv4Wire is the SonicOS on-wire representation of an IPv4 address object.
type AddressObjectIPv4Wire struct {
	Name    string                    `json:"name"`
	Zone    string                    `json:"zone"`
	Host    *addressObjectHostWire    `json:"host,omitempty"`
	Network *addressObjectNetworkWire `json:"network,omitempty"`
	Range   *addressObjectRangeWire   `json:"range,omitempty"`
	FQDN    *addressObjectFQDNWire    `json:"fqdn,omitempty"`
	MAC     *addressObjectMACWire     `json:"mac,omitempty"`
}

// AddressObjectEnvelope wraps an IPv4 address object in the SonicOS API envelope.
//
//	{"address_object": {"ipv4": {...}}}
type AddressObjectEnvelope struct {
	AddressObject struct {
		IPv4 AddressObjectIPv4Wire `json:"ipv4"`
	} `json:"address_object"`
}

// AddressObjectsListResponse is the SonicOS list response for address objects.
type AddressObjectsListResponse struct {
	AddressObjects []AddressObjectEnvelope `json:"address_objects"`
}

// maskToPrefixLen converts a dotted-decimal subnet mask to a CIDR prefix length.
func maskToPrefixLen(mask string) int {
	parts := [4]int{}
	_, _ = splitMask(mask, &parts)
	bits := 0
	for _, p := range parts {
		for p > 0 {
			bits += p & 1
			p >>= 1
		}
	}
	return bits
}

// splitMask parses a dotted-decimal mask into four octets.
func splitMask(mask string, parts *[4]int) (int, error) {
	n := 0
	cur := 0
	for i := 0; i <= len(mask); i++ {
		if i == len(mask) || mask[i] == '.' {
			if n < 4 {
				parts[n] = cur
			}
			n++
			cur = 0
		} else {
			cur = cur*10 + int(mask[i]-'0')
		}
	}
	return n, nil
}

// prefixLenToMask converts a CIDR prefix length to a dotted-decimal subnet mask.
func prefixLenToMask(prefix int) string {
	if prefix == 0 {
		return "0.0.0.0"
	}
	mask := ^uint32(0) << (32 - uint(prefix))
	return fmt.Sprintf("%d.%d.%d.%d",
		(mask>>24)&0xff,
		(mask>>16)&0xff,
		(mask>>8)&0xff,
		mask&0xff,
	)
}

// ToEnvelope converts an AddressObjectIPv4 to its SonicOS wire format envelope.
func (a *AddressObjectIPv4) ToEnvelope() AddressObjectEnvelope {
	wire := AddressObjectIPv4Wire{
		Name: a.Name,
		Zone: a.Zone,
	}

	switch a.Type {
	case AddressObjectTypeHost:
		wire.Host = &addressObjectHostWire{IP: a.Host}
	case AddressObjectTypeNetwork:
		// Parse CIDR: "10.0.0.0/24"
		subnet, prefix := splitCIDR(a.Network)
		wire.Network = &addressObjectNetworkWire{
			Subnet: subnet,
			Mask:   prefixLenToMask(prefix),
		}
	case AddressObjectTypeRange:
		wire.Range = &addressObjectRangeWire{Begin: a.RangeStart, End: a.RangeEnd}
	case AddressObjectTypeFQDN:
		wire.FQDN = &addressObjectFQDNWire{Domain: a.FQDN}
	case AddressObjectTypeMAC:
		wire.MAC = &addressObjectMACWire{Address: a.MAC}
	}

	env := AddressObjectEnvelope{}
	env.AddressObject.IPv4 = wire
	return env
}

// splitCIDR parses "subnet/prefix" and returns the subnet string and prefix length.
func splitCIDR(cidr string) (string, int) {
	for i := 0; i < len(cidr); i++ {
		if cidr[i] == '/' {
			prefix := 0
			for j := i + 1; j < len(cidr); j++ {
				prefix = prefix*10 + int(cidr[j]-'0')
			}
			return cidr[:i], prefix
		}
	}
	return cidr, 32
}

// FromWire converts a SonicOS wire-format AddressObjectIPv4Wire to AddressObjectIPv4.
func FromWire(wire AddressObjectIPv4Wire) *AddressObjectIPv4 {
	obj := &AddressObjectIPv4{
		Name: wire.Name,
		Zone: wire.Zone,
	}

	switch {
	case wire.Host != nil:
		obj.Type = AddressObjectTypeHost
		obj.Host = wire.Host.IP
	case wire.Network != nil:
		obj.Type = AddressObjectTypeNetwork
		prefixLen := maskToPrefixLen(wire.Network.Mask)
		obj.Network = fmt.Sprintf("%s/%d", wire.Network.Subnet, prefixLen)
	case wire.Range != nil:
		obj.Type = AddressObjectTypeRange
		obj.RangeStart = wire.Range.Begin
		obj.RangeEnd = wire.Range.End
	case wire.FQDN != nil:
		obj.Type = AddressObjectTypeFQDN
		obj.FQDN = wire.FQDN.Domain
	case wire.MAC != nil:
		obj.Type = AddressObjectTypeMAC
		obj.MAC = wire.MAC.Address
	}

	return obj
}